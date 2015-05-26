library(rjson)
library(RCurl)

getData <- function(num) {
    base.url <- "http://localhost:8080/api/plot"
    params <- paste0("?id=", num, "&begin=2001-01-01")
    url <- paste0(base.url, params)

    query <- getURL(url)
    res <- fromJSON(query, unexpected.escape = "skip")$results

    mu <- as.matrix(lapply(res, function(x) {return(x$inner$mu)}))
    date <- as.matrix(lapply(res, function(x) {return(x$date)}))

    return(data.frame(mu=mu, date=date))
}

plotCPI <- function(num) {
    data <- getData(num)
    date <- as.POSIXct(strptime(data$date, "%Y-%m-%d"))
    t <- ts(data['mu'], frequency=12, start=c(2001, 1))
    png("decomp.png", width=1000, height=1000, pointsize=30)
    plot(decompose(t))
    dev.off()
}