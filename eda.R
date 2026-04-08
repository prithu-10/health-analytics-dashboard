df <- read.csv("data/covid.csv")

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

df$Date <- as.Date(df$Date, format = "%Y-%m-%d")
df <- na.omit(df)
df <- df[order(df$Country, df$Date), ]

write.csv(df, "cleaned_data.csv", row.names = FALSE)

png("static/cases.png", width = 900, height = 500)
plot(df$Date, df$Cases, type = "l", col = "blue", lwd = 2,
     main = "Cases Over Time", xlab = "Date", ylab = "Cases")
dev.off()

png("static/deaths.png", width = 900, height = 500)
plot(df$Date, df$Deaths, type = "l", col = "red", lwd = 2,
     main = "Deaths Over Time", xlab = "Date", ylab = "Deaths")
dev.off()

png("static/vaccine.png", width = 900, height = 500)
plot(df$Date, df$Vaccinated, type = "l", col = "green", lwd = 2,
     main = "Vaccination Over Time", xlab = "Date", ylab = "Vaccinated")
dev.off()

png("static/trend.png", width = 900, height = 500)
plot(df$Date, df$Cases, type = "l", col = "purple", lwd = 2,
     main = "Overall COVID Trend", xlab = "Date", ylab = "Cases")
lines(df$Date, df$Deaths, col = "red", lwd = 2)
legend("topleft", legend = c("Cases", "Deaths"), col = c("purple", "red"), lwd = 2)
dev.off()

png("static/hist.png", width = 900, height = 500)
hist(df$Cases, col = "skyblue", border = "white",
     main = "Distribution of Cases", xlab = "Cases")
dev.off()

numeric_data <- df[, c(
  "Cases", "Deaths", "Vaccinated",
  "Population", "MedianAge",
  "HospitalBeds", "PositiveRate", "Stringency"
)]

corr_matrix <- cor(numeric_data)

if (!require("corrplot")) install.packages("corrplot", repos = "https://cloud.r-project.org")
library(corrplot)

png("static/heatmap.png", width = 900, height = 700)
corrplot(corr_matrix, method = "color", type = "upper", tl.col = "black", tl.cex = 0.8)
dev.off()

print("EDA DONE SUCCESSFULLY")
