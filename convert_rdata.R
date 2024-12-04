# Convert OFAC RData files to CSV

# Get all ofac_full RData files
files <- list.files(path = "data", 
                    pattern = "ofac_full_.*\\.RData$", 
                    full.names = TRUE)

# Convert each file
for (file in files) {
    load(file)
    
    csv_name <- sub("\\.RData$", ".csv", file)
    
    write.csv(ofac_full, csv_name, row.names = FALSE)
    
    rm(ofac_full)
}
