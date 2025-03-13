import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import json
from openai import OpenAI
from chromadb import Client
from chromadb.config import Settings

class VannaJSON:
    def __init__(self, api_key: str, model: str = "microsoft/phi-3-medium-128k-instruct", site_url: str = None, site_name: str = None, data_file: str = "data.json"):
        """
        Initialize the VannaJSON class.

        Args:
            api_key (str): API key for OpenRouter.
            model (str): The model to use for OpenRouter (default: "microsoft/phi-3-medium-128k-instruct").
            site_url (str, optional): URL for HTTP-Referer header.
            site_name (str, optional): Name for X-Title header.
            data_file (str): Path to the JSON file containing schema and examples (default: "data.json").
        """
        # Initialize API
        self.llm = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = model
        self.extra_headers = {}
        if site_url:
            self.extra_headers["HTTP-Referer"] = site_url
        if site_name:
            self.extra_headers["X-Title"] = site_name
        
        # Initialize ChromaDB in-memory
        self.db = Client(Settings())
        self.collection = self.db.get_or_create_collection(name="vanna_training")
        
        self.schema_json = None
        self.examples_file = "examples.json"
        self.data_file = data_file
        
        self.load_data()
        
        self.examples = {}
        try:
            with open(self.examples_file, "r") as f:
                self.examples = json.load(f)
                print(f"Loaded examples from {self.examples_file}")
        except FileNotFoundError:
            print(f"{self.examples_file} not found, starting with empty examples")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {self.examples_file}: {str(e)}. Starting with empty examples")
        except Exception as e:
            print(f"Error loading {self.examples_file}: {str(e)}. Starting with empty examples")

    def load_data(self):
        """
        Load schema and examples from data.json file.
        If the file is missing or invalid, initialize with empty values.
        """
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
                self.schema_json = data.get("schema", {})
                self.default_examples = data.get("examples", {})
                print(f"Loaded data from {self.data_file}")
        except FileNotFoundError:
            print(f"{self.data_file} not found, starting with empty schema and examples")
            self.schema_json = {}
            self.default_examples = {}
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {self.data_file}: {str(e)}. Starting with empty schema and examples")
            self.schema_json = {}
            self.default_examples = {}
        except Exception as e:
            print(f"Error loading {self.data_file}: {str(e)}. Starting with empty schema and examples")
            self.schema_json = {}
            self.default_examples = {}

    def train(self, schema: dict = None, documentation: str = None, examples: dict = None):
        """
        Train the model with schema, documentation, and examples.

        Args:
            schema (dict, optional): Schema to train on. If None, use schema from data.json.
            documentation (str, optional): Documentation to store in ChromaDB.
            examples (dict, optional): Examples to train on. If None, use examples from data.json.
        """
        if schema:
            self.schema_json = schema
        if not self.schema_json:
            self.schema_json = self.default_examples
        
        # Add schema to ChromaDB
        self.collection.add(
            ids=["schema"],
            documents=[json.dumps(self.schema_json)],
            metadatas=[{"type": "schema"}]
        )
        print("Added schema to ChromaDB")
        
        # Add documentation to ChromaDB if provided
        if documentation:
            self.collection.add(
                ids=["documentation"],
                documents=[documentation],
                metadatas=[{"type": "documentation"}]
            )
            print("Added documentation to ChromaDB")
        
        # Add examples to ChromaDB
        if examples:
            for question, json_query in examples.items():
                # Add example to ChromaDB
                self.collection.add(
                    ids=[f"example:{question}"],
                    documents=[json.dumps(json_query)],
                    metadatas=[{"type": "example", "question": question}]
                )
                print(f"Added example to ChromaDB: {question}")

                self.examples[question] = json_query
            
            with open(self.examples_file, "w") as f:
                json.dump(self.examples, f, indent=2)
            print(f"Saved examples to {self.examples_file}")

    def print_collection(self):
        """
        Print all records in the ChromaDB collection 'vanna_training'.
        Useful for debugging and verifying stored data.
        """
        print("Contents of ChromaDB collection 'vanna_training':")
        all_items = self.collection.get(include=["documents", "metadatas"])
        if not all_items["ids"]:
            print("Collection is empty")
            return
        for i in range(len(all_items["ids"])):
            print(f"ID: {all_items['ids'][i]}")
            print(f"Document: {all_items['documents'][i]}")
            print(f"Metadata: {all_items['metadatas'][i]}")
            print("---")

    def ask(self, question: str) -> str:
        """
        Generate a JSON query based on the user's question.

        Args:
            question (str): The user's question (e.g., "Find accounts with name Test").

        Returns:
            str: A JSON string representing the generated query.
        """
        # Query ChromaDB
        results = self.collection.query(
            query_texts=[question],
            n_results=2,
            where={"type": "example"}
        )
        example_context = ""
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                question_example = results["metadatas"][0][i]["question"]
                example_context += (
                    f"{i+1}. Question: '{question_example}'\n"
                    f"   Output: {doc}\n"
                )

        # Define the prompt
        prompt = (
            "You are an expert in generating JSON queries for a search interface based on user questions. "
            f"Given the following schema: {json.dumps(self.schema_json)}, You can not change the chema. Structure should be the same!"
            f"generate a JSON query for: '{question}'. "
            "The JSON object MUST follow this EXACT structure:\n"
            "{\n"
            "  \"version\": {\"majorRelease\": <int>, \"minorRelease\": <int>, \"patch\": <int>},\n"
            "  \"sortColumn\": {\"logicalName\": <string>, \"isAscSortOrder\": <boolean>},\n"
            "  \"sectionsList\": [{\"objectName\": \"Account\", \"label\": \"Account DETAILS\", \"isListView\": false, \"fieldsList\": [{\"logicalName\": <string>, \"operator\": \"=\", \"value\": <string>, \"type\": <string>, \"targetObject\": \"Account\", \"showRadiusDistance\": false, \"isListView\": false, \"isLabelEdited\": false}]}],\n"
            "  \"resultColumns\": [[{\"logicalName\": <string>, \"type\": <string>, \"targetObject\": \"Account\", \"label\": <string>, \"isSortable\": <boolean>, \"isRadiusDistance\": false, \"attribute\": <string>}],\n"
            "  \"matchAnySection\": false,\n"
            "  \"mapData\": {\"zoom\": 3.0, \"data\": {}, \"center\": {\"lat\": 42.87596410238256, \"lng\": -59.76562500000001}}\n"
            "}\n"
            "Rules:\n"
            "- Extract fields (e.g., 'Name', 'Site', 'Phone', 'OwnerId', 'Description') and values from the question.\n"
            "- Set 'logicalName' and 'attribute' to the field name (e.g., 'Name', 'Site').\n"
            "- Set 'type' based on the field: 'string' for Name/Site, 'phone' for Phone, 'reference' for OwnerId, 'textarea' for Description.\n"
            "- Set 'value' to the extracted value from the question as a string (e.g., 'Test', 'test.com').\n"
            "- Set 'operator' to '=' for all fields unless specified otherwise.\n"
            "- Include all fields from the schema in 'resultColumns' with default labels (e.g., 'Account Name' for 'Name').\n"
            "- Set 'sortColumn' to 'Name' with 'isAscSortOrder': false by default, unless sorting is specified (e.g., 'sorted by Site ascending' sets 'logicalName': 'Site', 'isAscSortOrder': true).\n"
            "- Use ONLY valid JSON values: strings in quotes, numbers as numbers, booleans as true/false.\n"
            "- Do NOT include any additional fields, duplicate sections, or invalid values (e.g., 'true' as a string or number).\n"
            "- If the output is invalid JSON or contains 'true' as a value for fields like 'value' or 'operator', regenerate with correct data types.\n"
            "- Return ONLY a single, valid JSON object starting with '{' and ending with '}'.\n"
            "Do NOT include any additional text, explanations, or formatting.\n\n"
            "Examples from training data:\n"
            f"{example_context if example_context else 'No training examples available.'}\n"
            "Additional examples:\n"
            "1. Question: 'Find accounts with name Test and site test.com'\n"
            "   Output: {\"version\":{\"majorRelease\":1,\"minorRelease\":8,\"patch\":0},\"sortColumn\":{\"logicalName\":\"Name\",\"isAscSortOrder\":false},\"sectionsList\":[{\"objectName\":\"Account\",\"label\":\"Account DETAILS\",\"isListView\":false,\"fieldsList\":[{\"logicalName\":\"Name\",\"operator\":\"=\",\"value\":\"Test\",\"type\":\"string\",\"targetObject\":\"Account\",\"showRadiusDistance\":false,\"isListView\":false,\"isLabelEdited\":false},{\"logicalName\":\"Site\",\"operator\":\"=\",\"value\":\"test.com\",\"type\":\"string\",\"targetObject\":\"Account\",\"showRadiusDistance\":false,\"isListView\":false,\"isLabelEdited\":false}]}],\"resultColumns\":[{\"logicalName\":\"Name\",\"type\":\"string\",\"targetObject\":\"Account\",\"label\":\"Account Name\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Name\"},{\"logicalName\":\"Site\",\"type\":\"string\",\"targetObject\":\"Account\",\"label\":\"Account Site\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Site\"},{\"logicalName\":\"Phone\",\"type\":\"phone\",\"targetObject\":\"Account\",\"label\":\"Account Phone\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Phone\"},{\"logicalName\":\"OwnerId\",\"type\":\"reference\",\"targetObject\":\"Account\",\"label\":\"Owner\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"OwnerId\"},{\"logicalName\":\"Description\",\"type\":\"textarea\",\"targetObject\":\"Account\",\"label\":\"Account Description\",\"isSortable\":false,\"isRadiusDistance\":false,\"attribute\":\"Description\"}],\"matchAnySection\":false,\"mapData\":{\"zoom\":3.0,\"data\":{},\"center\":{\"lat\":42.87596410238256,\"lng\":-59.76562500000001}}}\n"
            "2. Question: 'Find accounts with phone 4444 sorted by Site ascending'\n"
            "   Output: {\"version\":{\"majorRelease\":1,\"minorRelease\":8,\"patch\":0},\"sortColumn\":{\"logicalName\":\"Site\",\"isAscSortOrder\":true},\"sectionsList\":[{\"objectName\":\"Account\",\"label\":\"Account DETAILS\",\"isListView\":false,\"fieldsList\":[{\"logicalName\":\"Phone\",\"operator\":\"=\",\"value\":\"4444\",\"type\":\"phone\",\"targetObject\":\"Account\",\"showRadiusDistance\":false,\"isListView\":false,\"isLabelEdited\":false}]}],\"resultColumns\":[{\"logicalName\":\"Name\",\"type\":\"string\",\"targetObject\":\"Account\",\"label\":\"Account Name\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Name\"},{\"logicalName\":\"Site\",\"type\":\"string\",\"targetObject\":\"Account\",\"label\":\"Account Site\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Site\"},{\"logicalName\":\"Phone\",\"type\":\"phone\",\"targetObject\":\"Account\",\"label\":\"Account Phone\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Phone\"},{\"logicalName\":\"OwnerId\",\"type\":\"reference\",\"targetObject\":\"Account\",\"label\":\"Owner\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"OwnerId\"},{\"logicalName\":\"Description\",\"type\":\"textarea\",\"targetObject\":\"Account\",\"label\":\"Account Description\",\"isSortable\":false,\"isRadiusDistance\":false,\"attribute\":\"Description\"}],\"matchAnySection\":false,\"mapData\":{\"zoom\":3.0,\"data\":{},\"center\":{\"lat\":42.87596410238256,\"lng\":-59.76562500000001}}}\n"
            "3. Question: 'Find accounts with name Test, site test.com, phone 4444, and owned by Natalia Natalia'\n"
            "   Output: {\"version\":{\"majorRelease\":1,\"minorRelease\":8,\"patch\":0},\"sortColumn\":{\"logicalName\":\"Name\",\"isAscSortOrder\":false},\"sectionsList\":[{\"objectName\":\"Account\",\"label\":\"Account DETAILS\",\"isListView\":false,\"fieldsList\":[{\"logicalName\":\"Name\",\"operator\":\"=\",\"value\":\"Test\",\"type\":\"string\",\"targetObject\":\"Account\",\"showRadiusDistance\":false,\"isListView\":false,\"isLabelEdited\":false},{\"logicalName\":\"Site\",\"operator\":\"=\",\"value\":\"test.com\",\"type\":\"string\",\"targetObject\":\"Account\",\"showRadiusDistance\":false,\"isListView\":false,\"isLabelEdited\":false},{\"logicalName\":\"Phone\",\"operator\":\"=\",\"value\":\"4444\",\"type\":\"phone\",\"targetObject\":\"Account\",\"showRadiusDistance\":false,\"isListView\":false,\"isLabelEdited\":false},{\"logicalName\":\"OwnerId\",\"operator\":\"=\",\"value\":\"0055e000001TEdhAAG\",\"type\":\"reference\",\"targetObject\":\"Account\",\"showRadiusDistance\":false,\"isListView\":false,\"isLabelEdited\":false,\"lookupObject\":\"User\",\"isPolymorphicField\":false}]}],\"resultColumns\":[{\"logicalName\":\"Name\",\"type\":\"string\",\"targetObject\":\"Account\",\"label\":\"Account Name\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Name\"},{\"logicalName\":\"Site\",\"type\":\"string\",\"targetObject\":\"Account\",\"label\":\"Account Site\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Site\"},{\"logicalName\":\"Phone\",\"type\":\"phone\",\"targetObject\":\"Account\",\"label\":\"Account Phone\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"Phone\"},{\"logicalName\":\"OwnerId\",\"type\":\"reference\",\"targetObject\":\"Account\",\"label\":\"Owner\",\"isSortable\":true,\"isRadiusDistance\":false,\"attribute\":\"OwnerId\"},{\"logicalName\":\"Description\",\"type\":\"textarea\",\"targetObject\":\"Account\",\"label\":\"Account Description\",\"isSortable\":false,\"isRadiusDistance\":false,\"attribute\":\"Description\"}],\"matchAnySection\":false,\"mapData\":{\"zoom\":3.0,\"data\":{},\"center\":{\"lat\":42.87596410238256,\"lng\":-59.76562500000001}}}\n"
            f"Now, generate a JSON query for: '{question}'"
        )
        
        # Call the LLM
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            extra_headers=self.extra_headers,
            extra_body={},
            max_tokens=1000 
        )
        json_str = response.choices[0].message.content
        print(f"Raw LLM output for '{question}': {json_str}")
        return json_str

if __name__ == "__main__":
    vn = VannaJSON(
        api_key = os.getenv("OPENAI_API_KEY"),
        site_url="http://example.com",
        site_name="My Vanna App"
    )
    vn.train()  

    # Print the contents of ChromaDB
    vn.print_collection()
    
    # Test questions
    questions = [
        "Find accounts with name Test, site test.com, phone 4444, and owned by Natalia Natalia"
        # "Find accounts with phone 4444 sorted by Site ascending",
        # "Find accounts owned by Natalia Natalia sorted by Name descending"
    ]
    for q in questions:
        result = vn.ask(q)
        print(f"Question: {q}")
        print(f"Result (raw): {result}")
        print()