library(httr)
library(jsonlite)
library(dplyr)

# Main function to get SharePoint list data via REST API
get_sharepoint_list <- function(site_url, list_name, username, password, 
                               domain = NULL, select_fields = NULL, 
                               filter_query = NULL, order_by = NULL, 
                               top = NULL) {
  
  # Clean up site URL (remove trailing slash)
  site_url <- gsub("/$", "", site_url)
  
  # Construct the REST API endpoint
  api_endpoint <- paste0(site_url, "/_api/web/lists/getbytitle('", list_name, "')/items")
  
  # Build query parameters
  query_params <- list()
  
  if (!is.null(select_fields)) {
    query_params[["$select"]] <- paste(select_fields, collapse = ",")
  }
  
  if (!is.null(filter_query)) {
    query_params[["$filter"]] <- filter_query
  }
  
  if (!is.null(order_by)) {
    query_params[["$orderby"]] <- order_by
  }
  
  if (!is.null(top)) {
    query_params[["$top"]] <- as.character(top)
  }
  
  cat("API Endpoint:", api_endpoint, "\n")
  if (length(query_params) > 0) {
    cat("Query parameters:", paste(names(query_params), query_params, sep = "=", collapse = "&"), "\n")
  }
  
  # Try different authentication methods
  response <- try_sharepoint_auth(api_endpoint, username, password, domain, query_params)
  
  # Check response
  if (http_status(response)$category != "Success") {
    cat("Response status:", http_status(response)$message, "\n")
    cat("Response content:", content(response, "text"), "\n")
    stop("Failed to retrieve SharePoint data")
  }
  
  # Parse JSON response
  json_content <- content(response, "text", encoding = "UTF-8")
  parsed_data <- fromJSON(json_content)
  
  # Extract the actual data
  if ("d" %in% names(parsed_data) && "results" %in% names(parsed_data$d)) {
    # SharePoint 2013+ format
    result_data <- parsed_data$d$results
  } else if ("value" %in% names(parsed_data)) {
    # SharePoint Online modern format
    result_data <- parsed_data$value
  } else {
    # Fallback
    result_data <- parsed_data
  }
  
  # Convert to data frame if it's a list
  if (is.list(result_data) && !is.data.frame(result_data)) {
    result_data <- as.data.frame(do.call(rbind, lapply(result_data, function(x) {
      # Handle nested objects by converting to character
      x[sapply(x, is.list)] <- lapply(x[sapply(x, is.list)], function(y) {
        if (length(y) == 0) NA_character_ else as.character(y)
      })
      return(x)
    })))
  }
  
  cat("Retrieved", nrow(result_data), "rows with", ncol(result_data), "columns\n")
  
  return(result_data)
}

# Helper function to try different authentication methods
try_sharepoint_auth <- function(url, username, password, domain = NULL, query_params = NULL) {
  
  # Headers for SharePoint REST API
  headers <- add_headers(
    "Accept" = "application/json;odata=verbose",
    "Content-Type" = "application/json;odata=verbose"
  )
  
  # Format username for domain if provided
  auth_user <- if (!is.null(domain)) paste0(domain, "\\", username) else username
  
  # Try NTLM first (most common for SharePoint)
  cat("Trying NTLM authentication...\n")
  response <- try({
    GET(url,
        query = query_params,
        authenticate(auth_user, password, type = "ntlm"),
        headers,
        timeout(60))
  }, silent = TRUE)
  
  if (!inherits(response, "try-error") && http_status(response)$category == "Success") {
    return(response)
  }
  
  # Try Basic authentication
  cat("NTLM failed, trying Basic authentication...\n")
  response <- try({
    GET(url,
        query = query_params,
        authenticate(username, password, type = "basic"),
        headers,
        timeout(60))
  }, silent = TRUE)
  
  if (!inherits(response, "try-error") && http_status(response)$category == "Success") {
    return(response)
  }
  
  # Try Digest authentication
  cat("Basic failed, trying Digest authentication...\n")
  response <- try({
    GET(url,
        query = query_params,
        authenticate(username, password, type = "digest"),
        headers,
        timeout(60))
  }, silent = TRUE)
  
  if (inherits(response, "try-error")) {
    stop("All authentication methods failed")
  }
  
  return(response)
}

# Function to get list of all lists in a SharePoint site
get_sharepoint_lists <- function(site_url, username, password, domain = NULL) {
  
  site_url <- gsub("/$", "", site_url)
  api_endpoint <- paste0(site_url, "/_api/web/lists")
  
  response <- try_sharepoint_auth(api_endpoint, username, password, domain)
  
  if (http_status(response)$category != "Success") {
    stop("Failed to retrieve SharePoint lists")
  }
  
  json_content <- content(response, "text", encoding = "UTF-8")
  parsed_data <- fromJSON(json_content)
  
  # Extract list information
  if ("d" %in% names(parsed_data) && "results" %in% names(parsed_data$d)) {
    lists_data <- parsed_data$d$results
  } else if ("value" %in% names(parsed_data)) {
    lists_data <- parsed_data$value
  } else {
    lists_data <- parsed_data
  }
  
  # Return useful columns
  useful_cols <- c("Title", "Id", "ItemCount", "Created", "LastItemModifiedDate", "Hidden")
  available_cols <- intersect(useful_cols, names(lists_data))
  
  return(lists_data[, available_cols, drop = FALSE])
}

# Function to get list fields/columns
get_list_fields <- function(site_url, list_name, username, password, domain = NULL) {
  
  site_url <- gsub("/$", "", site_url)
  api_endpoint <- paste0(site_url, "/_api/web/lists/getbytitle('", list_name, "')/fields")
  
  response <- try_sharepoint_auth(api_endpoint, username, password, domain)
  
  if (http_status(response)$category != "Success") {
    stop("Failed to retrieve list fields")
  }
  
  json_content <- content(response, "text", encoding = "UTF-8")
  parsed_data <- fromJSON(json_content)
  
  if ("d" %in% names(parsed_data) && "results" %in% names(parsed_data$d)) {
    fields_data <- parsed_data$d$results
  } else if ("value" %in% names(parsed_data)) {
    fields_data <- parsed_data$value
  } else {
    fields_data <- parsed_data
  }
  
  # Return useful field information
  useful_cols <- c("Title", "InternalName", "TypeAsString", "Required", "Hidden")
  available_cols <- intersect(useful_cols, names(fields_data))
  
  return(fields_data[, available_cols, drop = FALSE])
}
