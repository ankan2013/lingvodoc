package ru.ispras.lingvodoc.frontend.app.controllers

import com.greencatsoft.angularjs.core.Scope
import com.greencatsoft.angularjs.{AbstractController, injectable}
import org.scalajs.dom._
import ru.ispras.lingvodoc.frontend.app.exceptions.ControllerException
import ru.ispras.lingvodoc.frontend.app.model.File
import ru.ispras.lingvodoc.frontend.app.services.{BackendService, ModalOptions, ModalService}
import ru.ispras.lingvodoc.frontend.app.utils.LingvodocExecutionContext.Implicits.executionContext

import scala.scalajs.js
import scala.scalajs.js.JSConverters._
import scala.scalajs.js.annotation.JSExport
import scala.scalajs.js.typedarray.ArrayBuffer
import scala.util.{Failure, Success}


@js.native
trait UserFilesScope extends Scope {
  var files: js.Array[File] = js.native
  var dataType: String = js.native
}


@injectable("UserFilesController")
class UserFilesController(scope: UserFilesScope, backend: BackendService) extends AbstractController[UserFilesScope](scope) {

  scope.files = js.Array[File]()
  scope.dataType = ""

  load()

  @JSExport
  def upload(file: org.scalajs.dom.raw.File) = {

    val formData = new FormData()
    formData.append("blob", file)
    formData.append("data_type", scope.dataType)

    backend.uploadFile(formData) onComplete  {
      case Success(id) =>
        backend.userFiles map {
          files =>
            files.find(_.getId == id.getId) foreach {
              file => scope.files.push(file)
          }
        }
      case Failure(e) => console.error(e.getMessage)
    }
  }

  private[this] def load() = {
    backend.userFiles onComplete {
      case Success(files) =>
        scope.files = files.toJSArray
      case Failure(e) =>
    }
  }
}
