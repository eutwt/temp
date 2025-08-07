library(httr)
library(jsonlite)

# Function to get SharePoint list data using REST API
get_sharepoint_list <- function(site_url, list_name, username, password) {
  # Construct REST API URL
  api_url <- paste0(site_url, "/_api/web/lists/getbytitle('", list_name, "')/items")
  
  # Make authenticated request
  response <- GET(
    api_url,
    authenticate(username, password, type = "basic"),
    add_headers("Accept" = "application/json;odata=verbose")
  )
  
  if (http_status(response)$category == "Success") {
    json_data <- fromJSON(content(response, "text"))
    return(json_data$d$results)
  } else {
    stop("Failed to retrieve SharePoint data")
  }
}
