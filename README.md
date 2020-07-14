# OMWebService API Documentation
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [OMWebService API Documentation](#omwebservice-api-documentation)
  - [Developer Guide](#developer-guide)
    - [Running Locally](#running-locally)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Introduction
OMWebService API documentation defined in [swagger-config.yaml](./src/swagger-config.yaml) using 
[OpenAPI Specification](https://swagger.io/specification/), rendered using [Swagger-UI](https://swagger.io/tools/swagger-ui/)
and deployed to AWS S3 to be viewed in the browser using this url: 
[https://omwebservice-api-docs-dev-docsbucket-63c7h6kaz6lp.s3.eu-central-1.amazonaws.com/index.html](https://omwebservice-api-docs-dev-docsbucket-63c7h6kaz6lp.s3.eu-central-1.amazonaws.com/index.html)

## Developer Guide
### Running Locally
```    
npm install
npm start
```

### Deploying Using Serverless Framework
#### Build for Deployment
```
npm run build
```
#### Init Serverless Stack
Doesn't need re-running each time. Only required once to create "serverless stack"
```
sls deploy
```
#### Deploy API-Docs to S3
```
sls s3deploy
```
#### Remove Serveless Stack
```
sls remove
```
