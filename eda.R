# Load dataset
df <- read.csv("data/covid.csv")

# Select columns
df <- df[, c(
  "location",
  "date",
  "total_cases",
  "total_deaths",
  "people_vaccinated",
  "population",
  "median_age",
  "hospital_beds_per_thousand",
  "positive_rate",
  "stringency_index"
)]

colnames(df) <- c(
  "Country", "Date", "Cases", "Deaths", "Vaccinated",
  "Population", "MedianAge", "HospitalBeds",
  "PositiveRate", "Stringency"
)

# Convert date
df$Date <- as.Date(df$Date, format="%Y-%m-%d")

# Remove NA
df <- na.omit(df)

# Save cleaned data
write.csv(df, "cleaned_data.csv", row.names=FALSE)

# ---------------- VISUALS ----------------

png("static/cases.png")
plot(df$Date, df$Cases, type="l", col="blue")
dev.off()

png("static/deaths.png")
plot(df$Date, df$Deaths, type="l", col="red")
dev.off()

png("static/vaccine.png")
plot(df$Date, df$Vaccinated, type="l", col="green")
dev.off()

# ---------------- HEATMAP ----------------

numeric_data <- df[, c(
  "Cases", "Deaths", "Vaccinated",
  "Population", "MedianAge",
  "HospitalBeds", "PositiveRate", "Stringency"
)]

corr_matrix <- cor(numeric_data)

if (!require("corrplot")) install.packages("corrplot")
library(corrplot)

png("static/heatmap.png", width=800, height=600)
corrplot(corr_matrix, method="color", type="upper")
dev.off()

print("EDA DONE SUCCESSFULLY")