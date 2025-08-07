# Function to parse IQY file structure
parse_iqy <- function(filepath) {
  lines <- readLines(filepath, warn = FALSE)
  
  result <- list(
    all_lines = lines,
    web_lines = lines[grepl("^WEB", lines, ignore.case = TRUE)],
    urls = lines[grepl("^http", lines, ignore.case = TRUE)],
    parameters = list()
  )
  
  # Extract key-value pairs
  for (line in lines) {
    if (grepl("=", line) && !grepl("^WEB", line, ignore.case = TRUE)) {
      parts <- strsplit(line, "=", fixed = TRUE)[[1]]
      if (length(parts) >= 2) {
        key <- trimws(parts[1])
        value <- trimws(paste(parts[-1], collapse = "="))
        result$parameters[[key]] <- value
      }
    }
  }
  
  return(result)
}

# Use it
iqy_data <- parse_iqy("your_file.iqy")

# See the structure
str(iqy_data)

# Look at specific parts
cat("URLs found:\n")
print(iqy_data$urls)

cat("\nParameters found:\n")



library(httr)
library(xml2)

# If you need authentication
response <- GET("your_xml_url_here", 
                authenticate("username", "password", type = "ntlm"))

# Parse the XML response
xml_content <- content(response, "parsed")

# Convert to data frame
rows <- xml_find_all(xml_content, ".//z:row")
df <- map_dfr(rows, ~ as.data.frame(t(xml_attrs(.x)), stringsAsFactors = FALSE))
print(iqy_data$parameters)
