package com.example

import akka.actor.ActorSystem
import akka.http.scaladsl.Http
import akka.http.scaladsl.model._
import akka.http.scaladsl.server.Directives._
import akka.stream.ActorMaterializer
import org.json4s._
import org.json4s.jackson.JsonMethods._
import org.json4s.jackson.Serialization
import org.json4s.jackson.Serialization.{read, write}

import scala.io.StdIn

case class CarQuery(is_new: Boolean, model: String, year: Int, max_mileage: Int)
case class Car(model: String, year: Int, price: Int, mileage: Int, promotion: Boolean)
case class SaveRequest(user_id: String, goal_data: Map[String, Any])

object SnowflakeMock extends App {
  implicit val system = ActorSystem("snowflake-mock")
  implicit val materializer = ActorMaterializer()
  implicit val executionContext = system.dispatcher
  implicit val formats = DefaultFormats

  // Mock data
  val carData = List(
    Car("Mercedes S-Class", 2025, 120000, 0, false),
    Car("Mercedes E-Class", 2024, 80000, 15000, true),
    Car("Maybach S-Class", 2023, 200000, 5000, false)
  )

  val route =
    path("query") {
      post {
        entity(as[String]) { json =>
          val query = read[CarQuery](json)
          val filtered = carData.filter { car =>
            car.year == query.year &&
            car.model == query.model &&
            car.mileage <= query.max_mileage
          }
          complete(HttpEntity(ContentTypes.`application/json`, write(filtered)))
        }
      }
    } ~
    path("save") {
      post {
        entity(as[String]) { json =>
          val request = read[SaveRequest](json)
          println(s"Mock: Saved data for user ${request.user_id}: ${request.goal_data}")
          complete(StatusCodes.OK)
        }
      }
    }

  val bindingFuture = Http().newServerAt("0.0.0.0", 8080).bind(route)

  println(s"Scala server running at http://localhost:8080/\nPress RETURN to stop...")
  StdIn.readLine()
  bindingFuture
    .flatMap(_.unbind())
    .onComplete(_ => system.terminate())
}