from xml.parsers.expat import ExpatError
from fastapi.responses import JSONResponse
import xmltodict

from fastapi import APIRouter, Body, HTTPException, status


xml_to_json_router = APIRouter()


@xml_to_json_router.post(
    "/xml_to_json", response_class=JSONResponse, summary="Converte XML em json"
)
def xml_to_json(xml_body: str = Body(..., media_type="application/xml")):
    """
    Converte uma string XML em json
    """
    if not xml_body or not xml_body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Corpo da requisição vazio!"
        )

    try:
        return xmltodict.parse(xml_input=xml_body)

    except ExpatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"XML malformado: {e}",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao converter para JSON: {e}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar o XML: {e}",
        )
