
# Develop OFAC Panel ------------------------------------------------------

library(magrittr)

source("R/format_ofac.R")

df <- generate_ofac_panel()

saveRDS(df, "ofac_panel.rds")
write.csv(df, "ofac_panel.csv", row.names = FALSE)
