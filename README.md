# RAG-powered telegram bot for real estate agency conversations

![How a generative model imagines the project](./BotPic.jpg)
##### How a generative model imagines the project
The project's core functionality resides within the "app" directory. The **Retrieval-Augmented Generation (RAG) chains** act as a bridge, integrating **vector databases** and a **generative language model** to offer contextually aware responses to user inquiries. The filters are designed to detect and record the presence of specific key phrases within any text-based input to send photos when required, whether it is a transcribed message or a regular text message. This is achieved by transcription occurring before applying filters while passing an outer middleware.
By transcribing the messages first, the filters can effectively identify and capture the desired keywords or phrases.
**docker-compose**.yml and **Dockerfile** files are used for containerization and deployment, allowing the application to be easily packaged and run in Docker containers.

Meanwhile, the "**hidden**" directory serves as a secure storage for sensitive data, including media files categorized by location and vector creation materials. The **vector stores** themselves are also located within this directory both for simple similarity search and self-query techniques.

### Local project tree
```
/home/user/
  ├── app/
  │   ├── context_vault/
  │   │   └── context_vault.py # Text data required for bot's replies and chains' operation (.gitignore)
  │   ├── filters/
  │   │   └── filters.py # To catch media files requests
  │   ├── handlers/
  │   │   ├── admin.py # Administrator access to the contents of user database.
  │   │   ├── chat.py # Manages chat-related operations: any text when filters return False, along with stiсkers and photos.
  │   │   ├── trigger.py # Processes trigger events.
  │   │   └── voice_processing.py # Handles any voice message processing.
  │   ├── middlewares/
  │   │   ├── inner.py
  │   │   └── outer.py
  │   ├── modules/
  │   │   └── chain_definition.py # Specifies the RAG chain.
  │   ├── utils/
  │   │   └── utils.py
  │   ├── docker-compose.yml
  │   ├── Dockerfile
  │   ├── main.py
  │   └── requirements.txt
  └── hidden/
      ├── proxy/
      │   └── nginx.conf
      └── data/
          ├── csv-items/
          │   └── metadata.csv
          ├── txt-docs/
          │   ├── doc1.txt
          │   └── doc2.txt
          ├── media/
          │   ├── city/
          │   ├── address-1/
          │   ├── address-2/
          │   ├── address-3/
          │   └── address-4/
          │   ...
          └── chroma-vectors/
              └── vector_stores/
                  └── db_rules/
                      ├── chroma.sqlite3
                      └── 80a586f9-3867-473d-85b0-be4e1177c2df
```

### Technologies used:
#### LangChain
LangChain to create multiple chains for different tasks, such as contextualizing questions, answering general questions about apartments, a company and performing various types of searches (e.g., description search, metadata search for prices). These chains were designed to handle specific aspects of the dialogue and information retrieval process. LangChain also helped in creating a history-aware retriever, which is responsible for retrieving relevant information based on the user's input and previous conversation history.

#### Dialogue manager 
A library to create an interactive menu where users answer a series of questions to provide preferences in services. The answers are used to create a prompt that is tailored to a company's needs, ensuring the prompt to be well-structured. Specifically, the prompt can provide the user with the cost for a specified number of guests or find a short description of the object. 
The description is generated automatically based on the metadata provided in the system table.

#### PostgreSQL
PostgreSQL is used to store chat message histories to take into account previous messages unique to each user, which enable the dialogue system to engage in more natural and interactive conversations with users. The database additionally stores information about users, specifically, their full names, mobile phones and also preferences in services they provide themselves while engaging in an interactive menu (trigger.py). Tables named "message store" and "users store" are connected to each other primarily by session_id, which is unique for each chat.

#### Qdrant Vector Store
Qdrant is used to create a vector store for metadata search. It allows a conversational chain to request additional information for each object about the price depended on the number of guests, as well as an apartment's detailed description.

#### Chroma Vector Store
Chroma is used to create a vector store for any stuff information. It is also used to split documents and create chunks for txt prices.