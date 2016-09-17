package ru.ispras.lingvodoc.frontend.app.controllers

import com.greencatsoft.angularjs.core.{Event, RouteParams, Scope}
import ru.ispras.lingvodoc.frontend.app.services.{BackendService, LexicalEntriesType, ModalOptions, ModalService}
import com.greencatsoft.angularjs.{AbstractController, injectable}
import org.scalajs.dom.console
import org.scalajs.dom.raw.HTMLInputElement
import ru.ispras.lingvodoc.frontend.app.controllers.common._
import ru.ispras.lingvodoc.frontend.app.exceptions.ControllerException
import ru.ispras.lingvodoc.frontend.app.model._
import ru.ispras.lingvodoc.frontend.app.utils.LingvodocExecutionContext.Implicits.executionContext

import scala.scalajs.js
import scala.scalajs.js.JSConverters._
import scala.scalajs.js.annotation.JSExport
import scala.util.{Failure, Success}
import ru.ispras.lingvodoc.frontend.app.utils.Utils

import scala.scalajs.js.UndefOr



@js.native
trait EditDictionaryScope extends Scope {

  var count: Int = js.native
  var offset: Int = js.native
  var size: Int = js.native

  var pageCount: Int = js.native

  var dictionaryTable: DictionaryTable = js.native

  var filter: String = js.native

  var enabledInputs: js.Array[Any] = js.native

}

@JSExport
@injectable("EditDictionaryController")
class EditDictionaryController(scope: EditDictionaryScope, params: RouteParams, modal: ModalService, backend: BackendService) extends
AbstractController[EditDictionaryScope](scope) {

  private[this] val dictionaryClientId = params.get("dictionaryClientId").get.toString.toInt
  private[this] val dictionaryObjectId = params.get("dictionaryObjectId").get.toString.toInt
  private[this] val perspectiveClientId = params.get("perspectiveClientId").get.toString.toInt
  private[this] val perspectiveObjectId = params.get("perspectiveObjectId").get.toString.toInt

  private[this] val dictionary = Dictionary.emptyDictionary(dictionaryClientId, dictionaryObjectId)
  private[this] val perspective = Perspective.emptyPerspective(perspectiveClientId, perspectiveObjectId)

  private[this] var enabledInputs: Seq[(String, String)] = Seq[(String, String)]()

  private[this] var dataTypes: Seq[TranslationGist] = Seq[TranslationGist]()
  private[this] var fields: Seq[Field] = Seq[Field]()

  //scope.count = 0
  scope.offset = 0
  scope.size = 5
  scope.pageCount = 0

  load()


  @JSExport
  def filterKeypress(event: Event) = {
    val e = event.asInstanceOf[org.scalajs.dom.raw.KeyboardEvent]
    if (e.keyCode == 13) {
      val query = e.target.asInstanceOf[HTMLInputElement].value
      loadSearch(query)
    }
  }


  @JSExport
  def loadPage(page: Int) = {
    val offset = (page - 1) * scope.size
    backend.getLexicalEntries(CompositeId.fromObject(dictionary), CompositeId.fromObject(perspective), LexicalEntriesType.All, offset, scope.size) onComplete {
      case Success(entries) =>
        scope.offset = offset
        scope.dictionaryTable = DictionaryTable.build(fields, dataTypes, entries)
      case Failure(e) => console.log(e.getMessage)
    }
  }

  @JSExport
  def loadSearch(query: String) = {
    backend.search(query, Some(CompositeId(perspectiveClientId, perspectiveObjectId)), tagsOnly = false) map {
      results =>
        console.log(results.toJSArray)
        val entries = results map(_.lexicalEntry)
        scope.dictionaryTable = DictionaryTable.build(fields, dataTypes, entries)
    }
  }

  @JSExport
  def range(min: Int, max: Int, step: Int) = {
    (min to max by step).toSeq.toJSArray
  }

  @JSExport
  def play(soundAddress: String, soundMarkupAddress: String) = {
    console.log(s"playing $soundAddress with markup $soundMarkupAddress")
  }

  @JSExport
  def viewSoundMarkup(soundAddress: String, soundMarkupAddress: String) = {
    val options = ModalOptions()
    options.templateUrl = "/static/templates/modal/soundMarkup.html"
    options.controller = "SoundMarkupController"
    options.backdrop = false
    options.keyboard = false
    options.size = "lg"
    options.resolve = js.Dynamic.literal(
      params = () => {
        js.Dynamic.literal(
          soundAddress = soundAddress.asInstanceOf[js.Object],
          dictionaryClientId = dictionaryClientId.asInstanceOf[js.Object],
          dictionaryObjectId = dictionaryObjectId.asInstanceOf[js.Object]
        )
      }
    ).asInstanceOf[js.Dictionary[js.Any]]

    val instance = modal.open[Unit](options)
  }

  @JSExport
  def addNewLexicalEntry() = {
    backend.createLexicalEntry(CompositeId.fromObject(dictionary), CompositeId.fromObject(perspective)) onComplete {
      case Success(entryId) =>
        backend.getLexicalEntry(CompositeId.fromObject(dictionary), CompositeId.fromObject(perspective), entryId) onComplete {
          case Success(entry) =>
            scope.dictionaryTable.addEntry(entry)
          case Failure(e) =>
        }
      case Failure(e) => throw ControllerException("Attempt to create a new lexical entry failed", e)
    }
  }

  @JSExport
  def dataTypeString(dataType: TranslationGist): String = {
    dataType.atoms.find(a => a.localeId == 2) match {
      case Some(atom) =>
        atom.content
      case None => throw new ControllerException("")
    }
  }

  @JSExport
  def enableInput(entry: LexicalEntry, field: Field) = {
    if (!isInputEnabled(entry, field))
      enabledInputs = enabledInputs :+ (entry.getId, field.getId)
  }

  @JSExport
  def disableInput(entry: LexicalEntry, field: Field) = {
    if (isInputEnabled(entry, field))
      enabledInputs = enabledInputs.filterNot(p => p._1 == entry.getId && p._2 == field.getId)
  }

  @JSExport
  def isInputEnabled(entry: LexicalEntry, field: Field): Boolean = {
    enabledInputs.exists(input => input._1 == entry.getId && input._2 == field.getId)
  }

  @JSExport
  def saveTextValue(entry: LexicalEntry, field: Field, event: Event, parent: UndefOr[Value]) = {

    val e = event.asInstanceOf[org.scalajs.dom.raw.Event]
    val textValue = e.target.asInstanceOf[HTMLInputElement].value

    val dictionaryId = CompositeId.fromObject(dictionary)
    val perspectiveId = CompositeId.fromObject(perspective)
    val entryId = CompositeId.fromObject(entry)

    val entity = EntityData(field.clientId, field.objectId, Utils.getLocale().getOrElse(2))
    entity.content = Some(Left(textValue))

    // self
    parent map {
      parentValue =>
        entity.selfClientId = Some(parentValue.getEntity.clientId)
        entity.selfObjectId = Some(parentValue.getEntity.objectId)
    }

    backend.createEntity(dictionaryId, perspectiveId, entryId, entity) onComplete {
      case Success(entityId) =>
        backend.getEntity(dictionaryId, perspectiveId, entryId, entityId) onComplete {
          case Success(newEntity) =>

            parent.toOption match {
              case Some(x) => scope.dictionaryTable.addEntity(entry, x.getEntity, newEntity)
              case None => scope.dictionaryTable.addEntity(entry, newEntity)
            }


            disableInput(entry, field)
          case Failure(ex) => console.log(ex.getMessage)
        }
      case Failure(ex) => console.log(ex.getMessage)
    }
  }

  @JSExport
  def saveFileValue(entry: LexicalEntry, field: Field, fileName: String, fileType: String, fileContent: String) = {
    val dictionaryId = CompositeId.fromObject(dictionary)
    val perspectiveId = CompositeId.fromObject(perspective)
    val entryId = CompositeId.fromObject(entry)

    val entity = EntityData(field.clientId, field.objectId, Utils.getLocale().getOrElse(2))
    entity.content = Some(Right(FileContent(fileName, fileType, fileContent)))
    backend.createEntity(dictionaryId, perspectiveId, entryId, entity) onComplete {
      case Success(entityId) =>
        backend.getEntity(dictionaryId, perspectiveId, entryId, entityId) onComplete {
          case Success(newEntity) =>
            scope.dictionaryTable.addEntity(entry, newEntity)
            disableInput(entry, field)
          case Failure(ex) => console.log(ex.getMessage)
        }
      case Failure(ex) => console.log(ex.getMessage)
    }

  }

  @JSExport
  def editLinkedPerspective(entry: LexicalEntry, field: Field, values: js.Array[Value]) = {

    val options = ModalOptions()
    options.templateUrl = "/static/templates/modal/editLinkedDictionary.html"
    options.controller = "EditDictionaryModalController"
    options.backdrop = false
    options.keyboard = false
    options.size = "lg"
    options.resolve = js.Dynamic.literal(
      params = () => {
        js.Dynamic.literal(
          dictionaryClientId = dictionaryClientId.asInstanceOf[js.Object],
          dictionaryObjectId = dictionaryObjectId.asInstanceOf[js.Object],
          perspectiveClientId = perspectiveClientId,
          perspectiveObjectId = perspectiveObjectId,
          linkPerspectiveClientId = field.link.get.clientId,
          linkPerspectiveObjectId = field.link.get.objectId,
          lexicalEntry = entry.asInstanceOf[js.Object],
          field = field.asInstanceOf[js.Object],
          links = values.map { _.asInstanceOf[GroupValue].link }
        )
      }
    ).asInstanceOf[js.Dictionary[js.Any]]

    val instance = modal.open[Seq[Entity]](options)
    instance.result map { entities =>
      entities.foreach(e => scope.dictionaryTable.addEntity(entry, e))
    }
  }

  private[this] def load() = {

    backend.dataTypes() onComplete {
      case Success(d) =>
        dataTypes = d
        backend.getFields(CompositeId.fromObject(dictionary), CompositeId.fromObject(perspective)) onComplete {
          case Success(f) =>
            fields = f
            backend.getLexicalEntriesCount(CompositeId.fromObject(dictionary), CompositeId.fromObject(perspective)) onComplete {
              case Success(count) =>
                //scope.count = count
                scope.pageCount = scala.math.ceil(count.toDouble / scope.size).toInt


                backend.getLexicalEntries(CompositeId.fromObject(dictionary), CompositeId.fromObject(perspective), LexicalEntriesType.All, scope.offset, scope.size) onComplete {
                  case Success(entries) =>
                    scope.dictionaryTable = DictionaryTable.build(fields, dataTypes, entries)
                  case Failure(e) => console.log(e.getMessage)
                }
              case Failure(e) => console.log(e.getMessage)
            }
          case Failure(e) => console.log(e.getMessage)
        }
      case Failure(e) => console.log(e.getMessage)
    }
  }


}
