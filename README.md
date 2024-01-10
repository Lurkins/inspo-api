# inspo-api

INSPO API is a python project built primarily to serve as the backend for the full INSPO application. INSPO allows you to capture ideas for future reference and inspiration. The API allows for user account creation and posting of text and photos to document anything inspiring. Made using Flask, Mongodb, and secured with JSON Web Tokens. 

<img src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Python3-powered_hello-world.svg" width="300">
<img src="https://upload.wikimedia.org/wikipedia/commons/3/3c/Flask_logo.svg" width="300">

## Endpoints: 

### Register user (POST)
/register

### login user (POST)
/auth

### Get all the items (GET)
/items

### Get a single item by ID (GET)
/items/{id}

### Add an item (POST)
/items

### Update an item's information (PUT)
/items/info/{id}

### Delete a item by ID (DELETE)
/items/{id}

