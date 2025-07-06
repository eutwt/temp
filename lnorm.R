# Method 1: Parametric approach using log-transformed data
calculate_lognormal_ci_parametric <- function(data, confidence_level = 0.98) {
  # Remove any non-positive values
  data <- data[data > 0]
  
  # Log-transform the data
  log_data <- log(data)
  
  # Calculate mean and standard error of log-transformed data
  n <- length(log_data)
  mean_log <- mean(log_data)
  sd_log <- sd(log_data)
  se_log <- sd_log / sqrt(n)
  
  # Calculate critical value
  alpha <- 1 - confidence_level
  t_critical <- qt(1 - alpha/2, df = n - 1)
  
  # Calculate CI on log scale
  ci_log_lower <- mean_log - t_critical * se_log
  ci_log_upper <- mean_log + t_critical * se_log
  
  # Transform back to original scale
  ci_lower <- exp(ci_log_lower)
  ci_upper <- exp(ci_log_upper)
  
  # Calculate point estimate (geometric mean)
  point_estimate <- exp(mean_log)
  
  return(list(
    lower = ci_lower,
    upper = ci_upper,
    point_estimate = point_estimate,
    confidence_level = confidence_level,
    n = n,
    mean_log = mean_log,
    sd_log = sd_log
  ))
}
