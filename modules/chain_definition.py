import os
import uuid
import psycopg
import qdrant_client

#Data Handling and Manipulation
import csv
import pandas as pd
import sys
import logging
from os import getenv
from dotenv import load_dotenv
from pathlib import Path
from huggingface_hub import login
from typing import Optional

# LangChain Components
from langchain_core.documents import Document
#from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader)
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter, 
    CharacterTextSplitter)

# Vectorization
from langchain_community.chat_models import GigaChat
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings.gigachat import GigaChatEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import (
    Chroma,
    Qdrant)
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from chromadb.config import Settings

from langchain.chains.query_constructor.base import AttributeInfo
from langchain.chains.query_constructor.base import(
    get_query_constructor_prompt, 
    StructuredQueryOutputParser)

# Retrievers
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.retrievers.self_query.qdrant import QdrantTranslator
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain.chains.query_constructor.base import (
    get_query_constructor_prompt, 
    StructuredQueryOutputParser
)
from langchain_community.document_transformers import (
    EmbeddingsRedundantFilter, 
    LongContextReorder)

# Conversation flow
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.messages import (
    SystemMessage,
    AIMessage, 
    HumanMessage)
from langchain.prompts import (
    ChatPromptTemplate,
    #FewShotChatMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain.chains import ConversationalRetrievalChain
from langchain.chains import (
    create_history_aware_retriever, 
    create_retrieval_chain)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

#Custom Utilities
from utils.utils import float_to_str, price_float_value, connect_to_db
from context_vault.context_vault import PROMPT_TEMPLATES, SELF_QUERY

from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain_core.messages import SystemMessage
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)

"""# chanks for csv prices"""

columns_to_embed = ['Описание']
columns_to_metadata = ['Адрес', 'Максимальное количество человек', 'Район', 'Стоимость аренды для одного человека', 'Стоимость аренды для двух человек', 'Стоимость аренды для трех человек']

docs = []
with open('/home/pino/perseus_chat/var/data/csv-items/metadata.csv', newline="", encoding='utf-8-sig') as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for i, row in enumerate(csv_reader):
        # Filter rows with empty values ​​in the column "Average_rent_cost_per_person"
        if row['Стоимость аренды для одного человека']:
            to_metadata = {col: row[col] for col in columns_to_metadata if col in row}
            values_to_embed = {k: row[k] for k in columns_to_embed if k in row}
            to_embed = "  ".join(f"{k.strip()}: {v.strip()}" for k, v in values_to_embed.items())
            newDoc = Document(page_content=to_embed, metadata=to_metadata)
            docs.append(newDoc)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=0,
)

csv_chunks = splitter.split_documents(docs)
#print(f"Example: {csv_chunks[3]}")

### Rules of residence chunks ###
def load_and_split_documents():
    directory_path = "/home/pino/perseus_chat/var/data/txt-docs/"
    loader = DirectoryLoader(directory_path, glob="*.txt", recursive=True, silent_errors=True, loader_cls=TextLoader)
    documents = loader.load() 
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=0,
    )
    documents = text_splitter.split_documents(documents)
    return documents

documents = load_and_split_documents()
print(f"Total chunks: {len(documents)}")

### Chroma.db vectorization in  ###
login(token=os.getenv("HF_TOKEN"))
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.abspath("/home/pino/perseus_chat/var/data/chroma-vectors/data")), "vector_stores")

def create_vectorstore(embeddings, documents, vectorstore_name):
    persist_directory = os.path.join(VECTOR_STORE_DIR, vectorstore_name)
    
    # Создание или загрузка векторной базы данных
    db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    
    return db

db_rules = create_vectorstore(
    embeddings=embeddings,
    documents=documents,
    vectorstore_name="db_rules",
)
print(f"{db_rules._collection.count()} chunks in chroma vector store.")

collection_name = "metadata_search"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GIGACHAT_TOKEN = os.getenv("GIGACHAT_TOKEN")

def read_csv_and_create_documents():
    columns_to_embed = ["Описание"]
    columns_to_metadata = ['Район', 'Адрес', 'Максимальное количество человек', 'Стоимость аренды для одного человека', 'Стоимость аренды для двух человек', 'Стоимость аренды для трех человек']

    docs = []
    with open('/home/pino/perseus_chat/var/data/csv-items/metadata.csv', newline="", encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for i, row in enumerate(csv_reader):
            if row['Стоимость аренды для одного человека']:
                to_metadata = {col: row[col] for col in columns_to_metadata if col in row}
                values_to_embed = {k: row[k] for k in columns_to_embed if k in row}

                new_doc = create_document(
                    row['Район'],
                    row['Адрес'],
                    float(row['Максимальное количество человек']),
                    float(row['Стоимость аренды для одного человека']),
                    float(row['Стоимость аренды для двух человек']),
                    row['Стоимость аренды для трех человек'] if 'Стоимость аренды для трех человек' in row else None,
                    "  ".join(values_to_embed.values())
                )
                docs.append(new_doc)
    return docs

def create_document(area, address, max_number_of_people, price_for_one_person, price_for_two_people, price_for_three_people, description):
    template = """Апартаменты находятся в {area} по адресу {address}. В квартире допустимо проживание не более {max_number_of_people} человек, а стоимость аренды для одного человека составит {price_for_one_person} рублей, для двух человек стоимость аренды: {price_for_two_people} рублей. """
    if price_for_three_people:
        template += """Стоимость для трех человек: {price_for_three_people} рублей."""

    template += """Обратите внимание, стоимость может меняться в зависимости от наличия праздников и выходных. Чем больше вы живете - тем меньше платите. Подробне о квартире: {description}"""

    final_text = template.format(area=area, address=address, max_number_of_people=float_to_str(max_number_of_people), price_for_one_person=price_for_one_person, price_for_two_people=price_for_two_people, price_for_three_people=price_for_three_people, description=description)

    metadata = {
        "area": area,
        "address": address,
        "max_number_of_people": float_to_str(max_number_of_people),
        "price_for_one_guest": float(price_for_one_person),
        "price_for_two_guests": float(price_for_two_people),
    }

    if price_for_three_people:
        metadata["price_for_three_guests"] = float(price_for_three_people)

    return Document(
        page_content=final_text,
        metadata=metadata
    )

rent_apartment_docs = read_csv_and_create_documents()
'''
def insert_data_to_vector_store(docs, collection_name: str, embeddings: Embeddings):
    Qdrant.from_documents(
        docs,
        embeddings,
        url=QDRANT_URL,
        prefer_grpc=True,
        api_key=QDRANT_API_KEY,
        collection_name=collection_name,
    )
    logger.debug("Data inserted successfully!!!")

insert_data_to_vector_store(rent_apartment_docs, collection_name, embeddings)
'''
"""**Building structured Query with Langchain**

"""
document_content_description = "Подробное описание квартиры для временной аренды"
attribute_info = SELF_QUERY['attribute-info'] 

"""**query_constructor**"""

llm = GigaChat(profanity_check=True, verify_ssl_certs=False, credentials=GIGACHAT_TOKEN)
'''
def get_query_constructor():
    prompt = get_query_constructor_prompt(document_content_description, attribute_info)
    output_parser = StructuredQueryOutputParser.from_components()
    query_constructor = prompt | llm | output_parser
    return query_constructor
'''
#user_query = "Стоимость для двоих человек квартиры по адресу ленина 27?"
#query_constructor = get_query_constructor()
#structured_query = query_constructor.invoke({"query": user_query})

"""Проблема: определил max_number_of_people как int.
Если этот query_constructor будет выполнен SelfQueryRetriever, он не сможет получить документы из векторного хранилища из-за несоответствия типов.
"""

#user_query = "Есть квартиры для одного человека?"
#query_constructor = get_query_constructor()
#structured_query = query_constructor.invoke({"query": user_query})

"""# inputs-ouputs pairs"""

def get_query_constructor():
    input_output_pairs = SELF_QUERY['input-output-pairs']

    prompt = get_query_constructor_prompt(document_content_description, attribute_info, examples = input_output_pairs)

    output_parser = StructuredQueryOutputParser.from_components()
    query_constructor = prompt | llm | output_parser
    return query_constructor

"""# SelfQueryRetriever

- Query constructor
- Qdrant vector store instance
- QdrantTranslator, which converts the structured query into a Qdrant filter clause.

"""

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
collection_name = "metadata_search"

def get_qdrant_vectorstore(
        embeddings: Embeddings,
        collection_name: str,
        content_payload_key: Optional[str] = "page_content") -> VectorStore:

    qdrantClient = qdrant_client.QdrantClient(
        url=QDRANT_URL,
        prefer_grpc=True,
        api_key=QDRANT_API_KEY)
    return QdrantVectorStore(qdrantClient, collection_name, embeddings, content_payload_key=content_payload_key)

def get_apartments_with_structured_query(user_query: str):
    vectorstore = get_qdrant_vectorstore(embeddings, collection_name)
    query_constructor = get_query_constructor()
    retriever = SelfQueryRetriever(
        query_constructor=query_constructor,
        vectorstore=vectorstore,
        structured_query_translator=QdrantTranslator(metadata_key="metadata"),
    )
    return retriever.invoke(user_query)

vectorstore = get_qdrant_vectorstore(embeddings, collection_name)
query_constructor = get_query_constructor()
retriever_items = SelfQueryRetriever(
     query_constructor=query_constructor,
     vectorstore=vectorstore,
     structured_query_translator=QdrantTranslator(metadata_key="metadata"),
     )

"""# retrievers
**compression_retriever**
"""

def Vectorstore_backed_retriever(vectorstore, search_type, k, score_threshold=None):
    search_kwargs={}
    if k is not None:
        search_kwargs['k'] = k
    if score_threshold is not None:
        search_kwargs['score_threshold'] = score_threshold

    retriever = vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs
    )
    return retriever

def create_compression_retriever(embeddings, base_retriever, chunk_size, k, similarity_threshold=None) -> ContextualCompressionRetriever:
    """
    Creates a retriever with compression capabilities for efficient context management.
    
    :param embeddings: Embedding model used for vectorizing text.
    :param base_retriever: The retriever to enhance with compression.
    :param chunk_size: Maximum number of characters in a text chunk.
    :param k: Number of documents to return in similarity search. A higher k provides more results but may include less relevant documents.
    :param similarity_threshold: Optional threshold to filter documents based on similarity. Documents with distance below this threshold are considered similar.
    :return: A retriever with compression capabilities.
    """
    splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=5, separator=". ")

    # Step 2: Create filters to remove redundant and irrelevant information
    redundant_filter = EmbeddingsRedundantFilter(embeddings=embeddings)
    relevant_filter = EmbeddingsFilter(embeddings=embeddings, k=k, similarity_threshold=similarity_threshold) 

    # Step 3: Reorder documents for better context flow
    reordering = LongContextReorder()
    
    # Step 4: Create a pipeline to process documents through the defined transformers
    pipeline_compressor = DocumentCompressorPipeline(
        transformers=[splitter, redundant_filter, relevant_filter, reordering]
    )

    # Step 5: Integrate the base retriever with the compression pipeline
    compression_retriever = ContextualCompressionRetriever( 
        base_compressor=pipeline_compressor,
        base_retriever=base_retriever
    )
    return compression_retriever

"""**for rules**
First case
"""

retriever = Vectorstore_backed_retriever(db_rules, "similarity", k=5)
DocumentCompression = create_compression_retriever(
    chunk_size=700,
    embeddings=embeddings,
    base_retriever=retriever,
    k=2,
)

retriever_DocumentCompression = DocumentCompression
retriever_DocumentCompression

"""Second case"""

retriever_rules = db_rules.as_retriever(search_kwargs={"k": 5})
retriever_rules

"""# Retriever Combination + Compression
**compression_retriever_reordered**
"""
'''
import os
from langchain.retrievers import (
    ContextualCompressionRetriever,
    MergerRetriever,
)
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain_community.vectorstores import Chroma
from langchain_community.document_transformers import (
    EmbeddingsClusteringFilter,
    EmbeddingsRedundantFilter,
)
from langchain_community.embeddings import HuggingFaceEmbeddings

lotr = MergerRetriever(retrievers=[retriever_items, retriever_rules])

filter = EmbeddingsRedundantFilter(embeddings=embeddings)
pipeline = DocumentCompressorPipeline(transformers=[filter])
compression_retriever = ContextualCompressionRetriever(
    base_compressor=pipeline, base_retriever=lotr
)


filter_ordered_cluster = EmbeddingsClusteringFilter(
    embeddings=embeddings,
    num_clusters=10,
    num_closest=1,
)

filter_ordered_by_retriever = EmbeddingsClusteringFilter(
    embeddings=embeddings,
    num_clusters=10,
    num_closest=1,
    sorted=True,
)

pipeline = DocumentCompressorPipeline(transformers=[filter_ordered_by_retriever])
compression_retriever = ContextualCompressionRetriever(
    base_compressor=pipeline, base_retriever=lotr
)

from langchain_community.document_transformers import LongContextReorder

filter = EmbeddingsRedundantFilter(embeddings=embeddings)
reordering = LongContextReorder()
pipeline = DocumentCompressorPipeline(transformers=[filter, reordering])
compression_retriever_reordered = ContextualCompressionRetriever(
    base_compressor=pipeline, base_retriever=lotr
)
'''
"""# PostgreSQL Chat Message History"""

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB_IP = os.getenv("POSTGRES_DB_IP")

table_name = "message_store"
conn_info = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_DB_IP}:5432/messages"
sync_connection = psycopg.connect(conn_info)

"""# chain для всех вопросов"""
### Contextualize question ###
contextualize_q_system_prompt = PROMPT_TEMPLATES['contextualize-q-system-prompt'] 

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, retriever_rules, contextualize_q_prompt
)

history_aware_retriever_for_description_search = create_history_aware_retriever(
    llm, retriever_items, contextualize_q_prompt
)

### Answer question ###
system_prompt = (
    f'{PROMPT_TEMPLATES["system-prompt"]}'
    '{context}')

#human_prompt = "Кратко изложите суть нашей беседы не более чем в 10 предложениях."
#human_message_template = HumanMessagePromptTemplate.from_template(human_prompt)

prompt = ChatPromptTemplate.from_messages(
   [
       ("system", system_prompt),
       MessagesPlaceholder(variable_name="chat_history"), #human_message_template,
       ("human", "{input}"),
   ]
)

### Answer question with description search ###
system_prompt_for_description_search  = (
    f'{PROMPT_TEMPLATES["system-prompt-for-description-search"]}'
    '{context}')


prompt_for_description_search = ChatPromptTemplate.from_messages(
   [
       ("system", system_prompt_for_description_search),
       MessagesPlaceholder(variable_name="chat_history"), 
       ("human", "{input}"),
   ]
)

### question_answer_chain ### 

question_answer_chain = create_stuff_documents_chain(llm, prompt) 
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

### question_answer_chain for descripton search: self-query retriever ###

question_answer_chain_for_description_search = create_stuff_documents_chain(
    llm, 
    prompt_for_description_search)

rag_chain_for_description_search = create_retrieval_chain(
    history_aware_retriever_for_description_search, 
    question_answer_chain_for_description_search)

table_name = "message_store"

def get_session_history(session_id: str) -> BaseChatMessageHistory:
   return PostgresChatMessageHistory(
        table_name,
        session_id,
        sync_connection=sync_connection
)

### conversational_rag_chain for general questions ### 
conversational_rag_chain = RunnableWithMessageHistory(
   rag_chain,
   get_session_history,
   input_messages_key="input",
   history_messages_key="chat_history",
   output_messages_key="answer",
)


### conversational_rag_chain for description search: self-query retriever ### 
conversational_rag_chain_for_description_search = RunnableWithMessageHistory(
   rag_chain_for_description_search,
   get_session_history,
   input_messages_key="input",
   history_messages_key="chat_history",
   output_messages_key="answer",
)

### conversational_rag_chain for metadata search: self-query retriever ### 
template = (f"{PROMPT_TEMPLATES['metadata-prompt']}\n\n"
            "Используй только следующие фрагменты извлеченные из базы данных (разделенные <data_base></data_base>), чтобы ответить на вопрос.\n" 
            "Текущий разговор:\n\n"
            "Фрагменты базы данных:\n" 
            "<data_base>\n"
            "{context}\n"
            "{chat_history}\n"
            "</data_base>\n\n"
            "Question: {question}\n"
            "Answer: """)

prompt = PromptTemplate(input_variables=['context', 'question'], template=template)

memory = ConversationBufferMemory(memory_key="chat_history",
                                  output_key="answer",
                                  return_messages=True,
                                  token_limit=0)

conversational_rag_chain_for_metadata_search = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever_items,
    combine_docs_chain_kwargs={"prompt": prompt},
    chain_type="stuff",
    return_source_documents=True,
    memory=memory, 
    verbose=True,
)