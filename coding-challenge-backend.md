# Coding Challenge

Please organize, design, document and test your code as if it would go into production. Please also add a Readme that documents how to set up the development environment and everything needed to get the API running. Then, please send us a link to the hosted repository for your project (GitHub, GitLab, Bitbucket, ...).

## moonBattery IoT Backend

The moonBattery is a new storage system which allows to store the energy produced by lunar-cells. Each moonBattery is registered with the moonBattery IoT backend. In this code-challenge we are going to develop the API of the backend with 3 endpoints.

### API Endpoints

- Register: This endpoint is to register a moonBattery during production of the battery. The moonBattery sends its unique MAC address and the backend returns a serial number (eg. 123456).

- Ping: The moonBattery periodically calls a ping endpoint of the backend. The backend stores the time of the last contact.

- Configurations: The moonBattery has an internal configuration database (key-value-pairs). When a configuration changes, the change is also sent to the backend. The endpoint should accept one or more configuration key-value-pairs.

These requirements are pretty high-level, so that you are flexible to make decisions on your own about details.

## Technology

You are free to develop the API in **Ruby, Python, Rust or Node.js**. You are welcome to use a web framework or database of your choice. Feel free to indicate your experience level with the language, framework and database, so that we can review accordingly.

## Bonus points: Authentication

Document in the Readme how you would secure the communication between moonBattery and backend for the different endpoints.
