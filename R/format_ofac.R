
# Aggregate ofac ----------------------------------------------------------

aggregate_ofac <- function(df, entity = FALSE){
  
  # df: an ofac_loc object
  
  if(entity){
    df <- df %>% 
      dplyr::filter(!(SDN_type %in% c("aircraft", "individual", "vessel")))
  }
  
  # TODO: replace West Bank, Palestinian, "Region: Gaza" with "West Bank & Gaza"
  
  ofac_agg <- df %>% 
    dplyr::group_by(Country, Rep_date) %>% 
    dplyr::summarize(Count = dplyr::n(), .groups = "drop") %>% 
    dplyr::ungroup()
  
  # TODO: add other records?
  filter_obs <- c(
    ofac_agg[which(startsWith(ofac_agg$Country, "-")),]$Country, 
    "undetermined",
    ofac_agg[which(startsWith(ofac_agg$Country, "Region")),]$Country
  )
  
  ofac_df <- ofac_agg %>% 
    dplyr::filter(!(Country %in% filter_obs))
  
  return(ofac_df)
  
}


# Get report dates --------------------------------------------------------

get_report_dates <- function(start = as.Date("2022-04-01"),
                             end = Sys.Date()){
  
  if(end > Sys.Date()){
    stop("Cannot select a future date!")
  }
  
  month_n <- lubridate::interval(start, end) %/% months(1)
  
  # If today is last day of month, add one
  if(end == lubridate::ceiling_date(end, unit = "month") - 1){
    month_n <- month_n + 1
  }
  
  dates_floor <- seq(start, by = "month", length.out = month_n)
  
  lubridate::ceiling_date(dates_floor, unit = "month") - 1
  
}


# Get file names ----------------------------------------------------------

get_file_names <- function(){
  paste0("data/ofac_loc_", get_report_dates(), ".rds")
}


# Generate ofac panel -----------------------------------------------------

generate_ofac_panel <- function(entity = FALSE){
  
  rep_dates <- get_file_names()
  
  ofac_df <- tibble::tibble()
  
  # TODO: add columns with and without entities
  
  for(i in seq_along(rep_dates)){
    ofac_df <- readRDS(rep_dates[i]) %>% 
      aggregate_ofac(entity = entity) %>% 
      rbind(ofac_df) %>% 
      dplyr::arrange(Country, Rep_date)
  }
  
  # Add date details
  ofac_df$yrqtr <- zoo::as.yearqtr(ofac_df$Rep_date)
  ofac_df$yrmon <- zoo::as.yearmon(ofac_df$Rep_date)
  
  # TODO: Add country codes 
  
  return(ofac_df)
  
}
