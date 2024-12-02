library(httr)
library(jsonlite)

get_okta_token_password <- function(okta_domain, 
                                  username, 
                                  password,
                                  scope = "openid profile") {
  
  # Construct the token endpoint URL
  token_url <- sprintf("https://%s/api/v1/authn", okta_domain)
  
  # Make the authentication request
  response <- POST(
    url = token_url,
    add_headers(
      "Accept" = "application/json",
      "Content-Type" = "application/json"
    ),
    body = list(
      username = username,
      password = password
    ),
    encode = "json"
  )
  
  # Check response status
  if (http_status(response)$category != "Success") {
    stop(sprintf("Authentication failed with status %d: %s", 
                status_code(response), 
                content(response, "text")))
  }
  
  # Parse the response
  auth_data <- fromJSON(rawToChar(response$content))
  
  return(auth_data)
}

# Example usage
tryCatch({
  token <- get_okta_token_password(
    okta_domain = "your-domain.okta.com",  # e.g., "company.okta.com"
    username = "your.email@company.com",
    password = "your_password"
  )
  
  # Print session token
  if (!is.null(token$sessionToken)) {
    cat("Successfully authenticated!\n")
    cat("Session Token:", token$sessionToken, "\n")
  }
  
}, error = function(e) {
  cat("Error:", e$message, "\n")
})