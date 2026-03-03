# API Reference (GraphQL)

## Base Endpoint

- URL: `http://localhost:8000/api/v1/graphql`
- Method: `POST`
- Body format: `{"query": "...", "variables": {...}}`
- Content-Type: `application/json`

For `me` query you must pass:

- `Authorization: Bearer <access_token>`

## Operations

### `register(inputData: RegisterInput!) -> TokenOutput`

Creates a user and returns JWT access token.

Input (`RegisterInput`):

- `username: String!`
- `email: String!`
- `password: String!`

Response (`TokenOutput`):

- `accessToken: String!`

Possible error messages:

- `username or email already exists`
- `password must be at least 8 characters`
- `password must contain at least one uppercase letter`
- `password must contain at least one lowercase letter`
- `password must contain at least one digit`
- `password must contain at least one special character`

### `login(inputData: LoginInput!) -> TokenOutput`

Authenticates user and returns JWT access token.

Input (`LoginInput`):

- `username: String!`
- `password: String!`

Response (`TokenOutput`):

- `accessToken: String!`

Possible error messages:

- `invalid credentials`

### `me -> UserOutput`

Returns current authenticated user.

Headers:

- `Authorization: Bearer <access_token>`

Response (`UserOutput`):

- `id: Int!`
- `username: String!`
- `email: String!`

Possible error messages:

- `authorization header is required`
- `invalid token`
- `user not found`

### `requestPasswordReset(inputData: RequestPasswordResetInput!) -> ResetTokenOutput`

Generates password reset token.

Input (`RequestPasswordResetInput`):

- `email: String!`

Response (`ResetTokenOutput`):

- `resetToken: String!`

Possible error messages:

- `try again later`

### `resetPassword(inputData: ConfirmPasswordResetInput!) -> Boolean`

Resets password by reset token.

Input (`ConfirmPasswordResetInput`):

- `token: String!`
- `newPassword: String!`

Response:

- `true` on success

Possible error messages:

- `invalid or expired token`
- `password must be at least 8 characters`
- `password must contain at least one uppercase letter`
- `password must contain at least one lowercase letter`
- `password must contain at least one digit`
- `password must contain at least one special character`

## Examples

### Register

```graphql
mutation Register($inputData: RegisterInput!) {
  register(inputData: $inputData) {
    accessToken
  }
}
```

```json
{
  "query": "mutation Register($inputData: RegisterInput!) { register(inputData: $inputData) { accessToken } }",
  "variables": {
    "inputData": {
      "username": "alex",
      "email": "alex@example.com",
      "password": "Verystrongpass1!"
    }
  }
}
```

### Login

```graphql
mutation Login($inputData: LoginInput!) {
  login(inputData: $inputData) {
    accessToken
  }
}
```

### Me

```graphql
query {
  me {
    id
    username
    email
  }
}
```

### Request Password Reset

```graphql
mutation RequestPasswordReset($inputData: RequestPasswordResetInput!) {
  requestPasswordReset(inputData: $inputData) {
    resetToken
  }
}
```

### Reset Password

```graphql
mutation ResetPassword($inputData: ConfirmPasswordResetInput!) {
  resetPassword(inputData: $inputData)
}
```
