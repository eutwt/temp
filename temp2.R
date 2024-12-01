library(httr2)
library(jsonlite)
library(tidyverse)

# Function to get ServiceNow demands
get_servicenow_demands <- function(instance_url, username, password, verify_ssl = FALSE, limit = 100) {
  # Build the request
  req <- request(paste0(instance_url, "/api/now/table/demand")) %>%
    req_headers(
      Accept = "application/json"
    ) %>%
    req_auth_basic(username, password) %>%
    # Disable SSL verification if needed
    req_options(
      ssl_verifypeer = verify_ssl,
      ssl_verifyhost = if(verify_ssl) 2 else 0
    ) %>%
    req_url_query(
      sysparm_limit = limit
    )
  
  # Perform the request and handle the response
  response <- tryCatch({
    req %>%
      req_perform() %>%
      resp_body_json()
  }, error = function(e) {
    # More detailed error handling
    if (grepl("SSL|TLS|certificate|handshake", e$message)) {
      stop(paste("SSL/TLS Error: Consider setting verify_ssl=FALSE if this is an internal instance.\n",
                 "Original error:", e$message))
    }
    stop(paste("API request failed:", e$message))
  })
  
  # Convert the response to a data frame
  if (!is.null(response$result)) {
    demands_df <- as.data.frame(do.call(rbind, response$result))
    return(demands_df)
  } else {
    stop("No results found in the response")
  }
}

# Example usage:
instance_url <- "https://now.zj.com"
username <- "your_username"
password <- "your_password"

# Try with SSL verification disabled
try({
  demands <- get_servicenow_demands(
    instance_url = instance_url,
    username = username,
    password = password,
    verify_ssl = FALSE  # Disable SSL verification
  )
  print(head(demands))
}, error = function(e) {
  message("Error fetching demands: ", e$message)
})
