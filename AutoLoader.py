
from langchain_community.document_loaders import BSHTMLLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_community.document_loaders import UnstructuredPowerPointLoader
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
import PyPDF2
from goose3 import Goose
import tempfile
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Website:
    def __init__(self, search):
        self.search = search
    
    def extract_text(self):
        g = Goose()
        article = g.extract(self.search)
        self.text = article.cleaned_text
        return self.text

class Youtube:
    def __init__(self, search):
        self.search = search
        
    def extract_text(self):
        self.text = YouTubeTranscriptApi.get_transcript(self.video_id, languages=['en'])
        return self.text

class Pdf:
    def __init__(self, documents_input=None):
        self.documents_input = documents_input
  
    def extract_text(self):
        if self.documents_input is not None:
            reader = PyPDF2.PdfReader(self.documents_input)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
            return text

class AutoLoaderDocument:
    def __init__(self, search = '', document=None, huge_file=False):
        """
        Constructor for AutoLoaderDocument
        
        Parameters
        ----------
        search : str
            The search query to use for downloading a webpage or YouTube video
        document : bytes
            The raw document to load
        huge_file : bool
            Whether the document is huge and needs to be loaded in chunks
        """
        self.document = document
        self.search = search
        self.huge_file = huge_file
        self.loaders = {
            'pdf': PyPDFLoader,
            'doc': UnstructuredWordDocumentLoader,
            'docx': UnstructuredWordDocumentLoader,
            'html': BSHTMLLoader,
            'ppt': UnstructuredPowerPointLoader,
            'pptx': UnstructuredPowerPointLoader
        }
    
    def extract_text(self):
        """
        Extract text from the document.

        If the document is uploaded, extract text from it directly.
        If the document is huge, split it into chunks of 4000 characters with an overlap of 400 characters.
        If the document is None, raise ValueError.
        If the document is of unsupported type, raise ValueError.
        Otherwise, return the extracted text as a string.
        """
        if self.document is not None:
            extension = self.document.name.split('.')[-1]
            if extension in self.loaders:
                loader_class = self.loaders[extension]
                # Save uploaded file to a temporary file
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(self.document.read())
                    tmp_file_path = tmp_file.name
                    print(tmp_file_path)
                    self.document_name = tmp_file.name
                
                doc = loader_class(tmp_file_path).load()
                if self.huge_file:
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=400)
                    doc = text_splitter.split_documents(doc)
                text = [doc[i].page_content for i in range(len(doc))]
                if isinstance(text, list):
                    text = " ".join(text)
                return text.encode("cp1252", errors="replace").decode("utf-8", errors="replace")
            else:
                raise ValueError('Unsupported file format.')
        else:
            raise ValueError('No document file provided.')