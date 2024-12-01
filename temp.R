library(httr2)
library(jsonlite)
library(tidyverse)

# Function to get ServiceNow demands
get_servicenow_demands <- function(instance_url, username, password, limit = 100) {
  # Build the request
  req <- request(paste0(instance_url, "/api/now/table/demand")) %>%
    req_headers(
      Accept = "application/json"
    ) %>%
    req_auth_basic(username, password) %>%
    req_url_query(
      sysparm_limit = limit,
      # You can add more query parameters as needed
      # sysparm_query = "active=true",
      # sysparm_fields = "number,short_description,state"
    )
  
  # Perform the request and handle the response
  response <- tryCatch({
    req %>%
      req_perform() %>%
      resp_body_json()
  }, error = function(e) {
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
# Replace these with your actual credentials
instance_url <- "https://now.zj.com"
username <- "your_username"
password <- "your_password"

# Get demands
try({
  demands <- get_servicenow_demands(instance_url, username, password)
  print(head(demands))
}, error = function(e) {
  message("Error fetching demands: ", e$message)
})
