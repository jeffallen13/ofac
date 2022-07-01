
# Develop OFAC Panel ------------------------------------------------------

source("R/format_ofac.R")

df <- generate_ofac_panel()

saveRDS(df, "data/ofac_panel.rds")
write.csv(df, "data/ofac_panel.csv", row.names = FALSE)
