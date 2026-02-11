---
layout: post
title: "API Test Automation with REST Assured: A Complete Guide"
date: 2026-02-05 14:30:00 +0000
categories: [automation, api-testing, java]
tags: [rest-assured, api, java, testing, microservices]
author: Hari Prasad
excerpt: "Master API test automation with REST Assured. Learn best practices for testing RESTful APIs, microservices, and implementing contract testing."
---

# API Test Automation with REST Assured: A Complete Guide

API testing is crucial in modern microservices architecture. REST Assured has become my go-to framework for API automation, and in this guide, I'll share the techniques that have helped me achieve 99.5% test reliability across 50+ microservices.

## Why REST Assured?

REST Assured brings several advantages to API testing:

- **Fluent API**: Readable, BDD-style syntax
- **Powerful assertions**: Built-in matchers and validators
- **Schema validation**: JSON and XML schema validation
- **Authentication support**: OAuth, Basic Auth, and more
- **Java ecosystem**: Seamless integration with TestNG/JUnit

## Getting Started

Add REST Assured to your Maven project:

```xml
<dependency>
    <groupId>io.rest-assured</groupId>
    <artifactId>rest-assured</artifactId>
    <version>5.3.0</version>
    <scope>test</scope>
</dependency>
```

## Basic GET Request

Here's a simple example testing a user API:

```java
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@Test
public void testGetUser() {
    given()
        .baseUri("https://api.example.com")
        .header("Authorization", "Bearer " + token)
        .pathParam("userId", 123)
    .when()
        .get("/users/{userId}")
    .then()
        .statusCode(200)
        .body("id", equalTo(123))
        .body("email", notNullValue())
        .body("status", equalTo("active"));
}
```

## POST Request with Request Body

Creating resources with validation:

```java
@Test
public void testCreateUser() {
    String requestBody = """
        {
            "name": "John Doe",
            "email": "john@example.com",
            "role": "admin"
        }
        """;
    
    given()
        .baseUri("https://api.example.com")
        .header("Content-Type", "application/json")
        .body(requestBody)
    .when()
        .post("/users")
    .then()
        .statusCode(201)
        .body("name", equalTo("John Doe"))
        .body("id", notNullValue())
        .body("createdAt", matchesPattern("\\d{4}-\\d{2}-\\d{2}.*"));
}
```

## Advanced Techniques

### 1. Extract and Reuse Response Data

```java
Response response = given()
    .baseUri("https://api.example.com")
    .body(createUserRequest)
.when()
    .post("/users")
.then()
    .statusCode(201)
    .extract().response();

int userId = response.path("id");
String email = response.path("email");

// Use in subsequent requests
given()
    .baseUri("https://api.example.com")
    .pathParam("userId", userId)
.when()
    .get("/users/{userId}")
.then()
    .body("email", equalTo(email));
```

### 2. JSON Schema Validation

```java
given()
    .baseUri("https://api.example.com")
.when()
    .get("/users/123")
.then()
    .statusCode(200)
    .body(matchesJsonSchemaInClasspath("schemas/user-schema.json"));
```

### 3. Request and Response Specifications

Create reusable specifications:

```java
public class APISpecs {
    public static RequestSpecification requestSpec() {
        return new RequestSpecBuilder()
            .setBaseUri("https://api.example.com")
            .setContentType(ContentType.JSON)
            .addHeader("Authorization", "Bearer " + getToken())
            .build();
    }
    
    public static ResponseSpecification responseSpec() {
        return new ResponseSpecBuilder()
            .expectResponseTime(lessThan(2000L))
            .expectContentType(ContentType.JSON)
            .build();
    }
}

// Usage
@Test
public void testWithSpecs() {
    given()
        .spec(APISpecs.requestSpec())
    .when()
        .get("/users/123")
    .then()
        .spec(APISpecs.responseSpec())
        .body("id", equalTo(123));
}
```

## Contract Testing with Pact

For microservices, I implement contract testing:

```java
@PactTestFor(providerName = "UserService")
public class UserServiceContractTest {
    
    @Pact(consumer = "OrderService")
    public RequestResponsePact createPact(PactDslWithProvider builder) {
        return builder
            .given("user exists")
            .uponReceiving("request for user")
            .path("/users/123")
            .method("GET")
            .willRespondWith()
            .status(200)
            .body(new PactDslJsonBody()
                .integerType("id", 123)
                .stringType("email", "user@example.com")
                .stringType("status", "active"))
            .toPact();
    }
    
    @Test
    void testUserExists(MockServer mockServer) {
        given()
            .baseUri(mockServer.getUrl())
        .when()
            .get("/users/123")
        .then()
            .statusCode(200)
            .body("id", equalTo(123));
    }
}
```

## Framework Architecture

Here's how I structure API test frameworks:

```
src/test/java/
├── api/
│   ├── clients/
│   │   ├── UserApiClient.java
│   │   └── OrderApiClient.java
│   ├── models/
│   │   ├── User.java
│   │   └── Order.java
│   └── specs/
│       └── APISpecs.java
├── tests/
│   ├── UserApiTests.java
│   └── OrderApiTests.java
└── utils/
    ├── TestDataGenerator.java
    └── AuthHelper.java
```

## Best Practices from Real Projects

### 1. Parallel Execution
```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <parallel>methods</parallel>
        <threadCount>10</threadCount>
    </configuration>
</plugin>
```

### 2. Environment Configuration
```java
public class Config {
    private static final String ENV = System.getProperty("env", "dev");
    
    public static String getBaseUri() {
        return switch(ENV) {
            case "prod" -> "https://api.production.com";
            case "staging" -> "https://api.staging.com";
            default -> "https://api.dev.com";
        };
    }
}
```

### 3. Logging and Reporting
```java
given()
    .filter(new RequestLoggingFilter())
    .filter(new ResponseLoggingFilter())
    .baseUri(baseUri)
.when()
    .get("/users/123");
```

## Real-World Results

In a recent financial services engagement:

- **Automated 3,000+ API test cases**
- **Achieved 99.5% reliability** (zero false positives)
- **Reduced API testing time from 2 days to 30 minutes**
- **Integrated with CI/CD** for continuous API validation
- **Implemented contract testing** for 50+ microservices

## CI/CD Integration

GitHub Actions example:

```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
      - name: Run API Tests
        run: mvn test -Dtest=**/*ApiTest
      - name: Publish Test Report
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: API Test Results
          path: target/surefire-reports/*.xml
          reporter: java-junit
```

## Conclusion

REST Assured provides everything you need for robust API test automation. Combined with proper framework architecture and best practices, you can achieve enterprise-grade API testing that scales with your microservices architecture.

Next week, I'll cover advanced topics including performance testing with Gatling and chaos engineering for APIs.

---

**Want to discuss API testing strategies?** Reach out on [LinkedIn](https://www.linkedin.com/in/hariprasadms/) or explore my [API testing frameworks on GitHub](https://github.com/hariprasadms).

*Hari Prasad specializes in building scalable test automation solutions for enterprises through SDET Experts Pvt Ltd.*
