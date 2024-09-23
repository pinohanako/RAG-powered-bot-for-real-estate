# RAG-powered telegram bot for real estate agency conversations
![How a generative model imagines the project](./BotPic.jpg)
##### How a generative model imagines the project

The project is aimed at automating and streamlining daily conversations with clients concerning frequently asked questions about the rules of residence, booking, real estate and selection of suitable properties for a user. 
For the purpose, two types of retrievers and three langchains were used because it was necessary to set different prompts and perform different types of search depending on the state in the dialogue. 

#### A list of functions the project could offer
### Context-Sensitive Text Generation: 
The system can generate personalized and contextually relevant text about a specific company or real estate project. It can provide detailed information, highlight unique features, and tailor the content to the user's interests and previous interactions.

### Voice Message Recognition and Response
The system can accurately interpret and respond to voice messages. Users can ask questions, make requests, or provide feedback through voice commands, and the system will generate appropriate responses.

### Real Estate Photo Sharing
Upon request, either through text or voice, the system can send photos of real estate objects.

### Cost Estimation Based on Guest Characteristics
By analyzing user preferences, guest profiles, and property attributes, the system can estimate the cost of a real estate object. It takes into account factors like the number of guests, age, and other specific requirements to provide an accurate cost estimate.

### Natural Language-Based Property Selection
Users can express their preferences and requirements in natural language, and the system will interpret and match them with suitable real estate options. It understands user intent, considers various factors, and presents a curated list of properties that align with their preferences.

### User Message and Preference Storage
All text messages exchanged between users and the system, along with user preferences and service choices, are stored in a secure database. This data is used to personalize future interactions, send notifications to administrators and offer a seamless user experience across multiple sessions.

### Joke Imitation and Sticker/Photo Response
To add a touch of humor and engagement, the system can respond to stickers and photos sent by users with witty jokes or humorous comments. 

## A breakdown of the project components and their functionalities:

### Retriever Types
#### Similarity Search with Compression
This retriever is designed to handle general questions and conversations. It utilizes a compression technique to efficiently search for relevant information based on the user's input, whether it's text or voice.
#### Self-Query Retriever
Two instances of the self-query retriever have implemented for specific tasks:
#### Metadata Search
This retriever is triggered when a user wants to know the cost of a property. It asks the user a series of four questions (using the aiogram-dialog framework) to gather the necessary information to calculate the final cost.
#### Description Search
Another instance of the self-query retriever is employed when a user seeks a detailed description of a property. It likely retrieves and presents comprehensive information about the property's features and characteristics.

### Langchains
#### Conversational RAG Chain for General Questions
This langchain utilizes the similarity search retriever to handle a wide range of user inquiries. It aims to provide accurate and contextually relevant responses to general questions about residence rules, booking processes, and real estate.
#### Conversational RAG Chain for Metadata Search
Here, the self-query retriever is integrated to guide users through the process of determining the cost of a property. By asking a set of questions, it collects the required details to calculate and present the final cost.
#### Conversational RAG Chain for Description Search
This langchain, equipped with the self-query retriever, assists users in obtaining comprehensive descriptions of properties. It retrieves and presents detailed information, ensuring users have a clear understanding of the property's attributes.

### Other technologies used:
#### Aiogram-dialog 
A library to create an interactive menu where users answer a series of questions to provide preferences in services. The answers are used to create a prompt, ensuring the prompt to be well-structured and tailored to a company's needs. Specifically, a prompt behind the interface allows langchains to form a structured request and answer a user's question about the rental price, depending on the information provided in the interactive menu, and also to find a short description of an object. Descriptions are generated automatically based on the metadata provided in a csv table.

#### PostgreSQL
PostgreSQL is used to store chat message histories to take into account previous messages unique to each user, which enable the dialogue system to engage in more natural conversations with users. The database additionally stores information about users, specifically, their full names, mobile phones (if provided) and also preferences in services they provide while engaging in an interactive menu (trigger.py). Tables named "message store" and "user store" are connected to each other primarily by session_id unique for each chat.

#### Qdrant Vector Store
Qdrant is used to create a vector store for metadata search. It allows a conversational chain to request additional information for each object about the price depended on the number of guests, as well as an apartment's detailed description.

#### Chroma Vector Store
Chroma is used to create a vector store for any stuff information. It is also used to split documents and create chunks for txt prices.

The project's core functionality resides within an "app" directory. The **Retrieval-Augmented Generation (RAG) chains** act as a bridge, integrating **vector databases** and a **generative language model** to offer contextually aware responses to user inquiries. The filters are designed to detect and record the presence of specific key phrases within any text-based input to send photos when required, whether it is a transcribed message or a regular text message. This is achieved by transcription occurring before applying filters while passing an outer middleware.
By transcribing the messages first, the filters can effectively identify and capture the desired keywords or phrases to catch an intent and trigger specified handlers.
**docker-compose**.yml and **Dockerfile** files are used for containerization and deployment.

Meanwhile, the "**hidden**" directory serves as a secure storage for sensitive data mounted to the main directory, including media files categorized by location and vector creation materials. 
The **vector stores** themselves are also located within this directory both for simple similarity search and self-query techniques.

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

