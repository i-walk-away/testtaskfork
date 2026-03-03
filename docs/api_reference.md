# API-референс (GraphQL)

## Общая информация

- Endpoint: `http://localhost:8000/api/v1/graphql`
- Метод: `POST`
- Формат тела: `{"query": "...", "variables": {...}}`
- Content-Type: `application/json`

Важно:

- Все бизнес-операции выполняются через один GraphQL endpoint.
- Для запроса `me` обязателен заголовок `Authorization: Bearer <access_token>`.

## Операции

### 1. Регистрация

Операция: `register(inputData: RegisterInput!) -> TokenOutput`

Входные параметры (`RegisterInput`):

- `username: String!`
- `email: String!`
- `password: String!`

Успешный ответ (`TokenOutput`):

- `accessToken: String!`

Возможные ошибки:

- `username or email already exists`
- `password must be at least 8 characters`
- `password must contain at least one uppercase letter`
- `password must contain at least one lowercase letter`
- `password must contain at least one digit`
- `password must contain at least one special character`

Пример GraphQL запроса:

```graphql
mutation Register($inputData: RegisterInput!) {
  register(inputData: $inputData) {
    accessToken
  }
}
```

Пример HTTP payload:

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

### 2. Авторизация

Операция: `login(inputData: LoginInput!) -> TokenOutput`

Входные параметры (`LoginInput`):

- `username: String!`
- `password: String!`

Успешный ответ (`TokenOutput`):

- `accessToken: String!`

Возможные ошибки:

- `invalid credentials`

Пример GraphQL запроса:

```graphql
mutation Login($inputData: LoginInput!) {
  login(inputData: $inputData) {
    accessToken
  }
}
```

Пример HTTP payload:

```json
{
  "query": "mutation Login($inputData: LoginInput!) { login(inputData: $inputData) { accessToken } }",
  "variables": {
    "inputData": {
      "username": "alex",
      "password": "Verystrongpass1!"
    }
  }
}
```

### 3. Профиль текущего пользователя

Операция: `me -> UserOutput`

Требования:

- заголовок `Authorization: Bearer <access_token>`

Успешный ответ (`UserOutput`):

- `id: Int!`
- `username: String!`
- `email: String!`

Возможные ошибки:

- `authorization header is required`
- `invalid token`
- `user not found`

Пример GraphQL запроса:

```graphql
query {
  me {
    id
    username
    email
  }
}
```

Пример HTTP payload:

```json
{
  "query": "query { me { id username email } }"
}
```

### 4. Запрос на сброс пароля

Операция: `requestPasswordReset(inputData: RequestPasswordResetInput!) -> ResetTokenOutput`

Входные параметры (`RequestPasswordResetInput`):

- `email: String!`

Успешный ответ (`ResetTokenOutput`):

- `resetToken: String!`

Возможные ошибки:

- `try again later`

Пример GraphQL запроса:

```graphql
mutation RequestPasswordReset($inputData: RequestPasswordResetInput!) {
  requestPasswordReset(inputData: $inputData) {
    resetToken
  }
}
```

Пример HTTP payload:

```json
{
  "query": "mutation RequestPasswordReset($inputData: RequestPasswordResetInput!) { requestPasswordReset(inputData: $inputData) { resetToken } }",
  "variables": {
    "inputData": {
      "email": "alex@example.com"
    }
  }
}
```

### 5. Подтверждение сброса пароля

Операция: `resetPassword(inputData: ConfirmPasswordResetInput!) -> Boolean`

Входные параметры (`ConfirmPasswordResetInput`):

- `token: String!`
- `newPassword: String!`

Успешный ответ:

- `true`

Возможные ошибки:

- `invalid or expired token`
- `password must be at least 8 characters`
- `password must contain at least one uppercase letter`
- `password must contain at least one lowercase letter`
- `password must contain at least one digit`
- `password must contain at least one special character`

Пример GraphQL запроса:

```graphql
mutation ResetPassword($inputData: ConfirmPasswordResetInput!) {
  resetPassword(inputData: $inputData)
}
```

Пример HTTP payload:

```json
{
  "query": "mutation ResetPassword($inputData: ConfirmPasswordResetInput!) { resetPassword(inputData: $inputData) }",
  "variables": {
    "inputData": {
      "token": "<reset_token>",
      "newPassword": "Newstrongpass2!"
    }
  }
}
```
