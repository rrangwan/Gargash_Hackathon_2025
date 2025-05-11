name := "snowflake-mock-service"

version := "1.0"

scalaVersion := "2.13.7"

libraryDependencies ++= Seq(
  "com.typesafe.akka" %% "akka-http" % "10.2.7",
  "com.typesafe.akka" %% "akka-stream" % "2.6.17",
  "com.typesafe" % "config" % "1.4.1",
  "org.json4s" %% "json4s-jackson" % "4.0.3"
)

// Ensure SBT uses the correct resolver
resolvers += "Akka Repository" at "https://repo.akka.io/maven"