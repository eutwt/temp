# Install required packages if not already installed
if (!require("httr")) install.packages("httr")
if (!require("jsonlite")) install.packages("jsonlite")

library(httr)
library(jsonlite)

get_okta_token <- function(okta_domain, 
                          auth_server_id = "default", # Use "default" or your custom server ID
                          client_id,
                          client_secret,
                          scope = "openid profile") {
  
  # Construct the token endpoint URL
  token_url <- sprintf("https://%s/oauth2/%s/v1/token",
                      okta_domain,
                      auth_server_id)
  
  # Create the authentication header
  auth_header <- sprintf("Basic %s",
                        base64enc::base64encode(charToRaw(paste0(client_id, ":", client_secret))))
  
  # Make the POST request
  response <- tryCatch({
    POST(
      url = token_url,
      add_headers(
        "Accept" = "application/json",
        "Authorization" = auth_header,
        "Content-Type" = "application/x-www-form-urlencoded"
      ),
      body = list(
        grant_type = "client_credentials",
        scope = scope
      ),
      encode = "form"
    )
  }, error = function(e) {
    stop(sprintf("Request failed: %s", e$message))
  })
  
  # Check response status
  if (http_status(response)$category != "Success") {
    stop(sprintf("Request failed with status %d: %s", 
                status_code(response), 
                content(response, "text")))
  }
  
  # Parse and return the response
  token_data <- fromJSON(rawToChar(response$content))
  return(token_data)
}

# Example usage:
# Replace these values with your actual Okta credentials
config <- list(
  okta_domain = "your-domain.okta.com",
  auth_server_id = "default",  # or your custom server ID
  client_id = "your_client_id",
  client_secret = "your_client_secret",
  scope = "openid profile"
)

# Get the token
tryCatch({
  token <- get_okta_token(
    okta_domain = config$okta_domain,
    auth_server_id = config$auth_server_id,
    client_id = config$client_id,
    client_secret = config$client_secret,
    scope = config$scope
  )
  
  # Print token details
  cat("Access Token:", token$access_token, "\n")
  cat("Token Type:", token$token_type, "\n")
  cat("Expires in:", token$expires_in, "seconds\n")
  
}, error = function(e) {
  cat("Error:", e$message, "\n")
})