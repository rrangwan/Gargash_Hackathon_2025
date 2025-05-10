name := "scala-webapp-component"
version := "0.1.0"
scalaVersion := "2.13.8"

// Add your Scala dependencies here
libraryDependencies ++= Seq(
  "org.scala-lang" % "scala-library" % scalaVersion.value,
  "com.typesafe.akka" %% "akka-actor" % "2.6.19",
  "com.typesafe.akka" %% "akka-http" % "10.2.9",
  "com.typesafe.akka" %% "akka-stream" % "2.6.19",
  "com.typesafe.play" %% "play-json" % "2.9.3"
)

// Assembly settings
assemblyJarName in assembly := s"${name.value}-${version.value}.jar"