package com.example

object Main {
  def main(args: Array[String]): Unit = {
    println("Scala component initialized")
  }
  
  def processData(data: String): String = {
    // Sample data processing function
    s"Processed: $data"
  }
}