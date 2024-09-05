from io import BytesIO
from typing import Literal, Optional, Union

from pybliometrics.superclasses import Retrieval
from pybliometrics.utils import (
    chained_get,
    check_parameter_value,
    detect_id_type,
    VIEWS,
)

class SpecificObjectRetrieval(Retrieval):
    def __init__(self, 
                 identifier: str,
                 mime_type: str,
                 id_type: str,
                 refresh: Union[bool, int] = False):
        """Class to retrieve a specific object of a document."""
        self._view = ''
        self._refresh = refresh
        super().__init__(identifier,
                         'ObjectRetrieval',
                         id_type,
                         httpAccept=mime_type)
        self._object = BytesIO(self._object)


class ObjectRetrieval(Retrieval):
    def get_specific_object(self,
                            ref: str,
                            mime_type: Optional[str] = None,
                            img_type: Optional[Literal['thumbnail', 'standard', 'high']] = None,
                            ) -> BytesIO:
        """Retrieves a specific object of a document.

        :param ref: The reference of the object. This is the `ref` field in the object_references.
        :param mime_type: The MIME type of the object. If not supplied, it will be determined automatically.
        :param img_type: Can be used ff the object is an image. The type of image to retrieve. Allowed values: `thumbnail`, `standard`, `high`.
        """
        if not mime_type:
            mime_type = self._find_mime_type(ref)
        
        if not img_type:
            identifier = f'{self.identifier}/ref/{ref}/standard'
        else:
            identifier = f'{self.identifier}/ref/{ref}/high'
        
        spe_obj = SpecificObjectRetrieval(identifier=identifier,
                                          mime_type=mime_type,
                                          id_type=self.id_type,
                                          refresh=self._refresh)
        return spe_obj._object


    @property
    def object_references(self):
        """List with metadata of objects in a document. The metadata includes the `url`, `eid`,
        `ref`, `filename`, `mimetype`, `size`, `height`, `width`, and `type` of the object.
        """
        refs = chained_get(self._json, ['attachment-metadata-response', 'attachment'])
        out = []
        for ref in refs:
            out.append({'url': ref.get('prism:url'),
                        'eid': ref.get('eid'),
                        'ref': ref.get('ref'),
                        'filename': ref.get('filename'),
                        'mimetype': ref.get('mimetype'),
                        'size': ref.get('size'),
                        'height': ref.get('height'),
                        'width': ref.get('width'),
                        'type': ref.get('type')})
        return out


    def __init__(self,
                 identifier: Union[int, str],
                 view: str = 'META',
                 id_type: Optional[str] = None,
                 refresh: Union[bool, int] = False,
                 **kwds: str
                 ):
        """Class to retrieve a specific object of a document or its metadata.

        :param identifier: The indentifier of an article.
        :param view: The view of the object. Allowed values: META.
        :param id_type: The type of identifier supplied. Allowed values: doi, pii, scopus_id, pubmed_id, eid.
        :param refresh: Whether to refresh the cached file if it exists. Default: False.
        """
        self.identifier = str(identifier)
        check_parameter_value(view, VIEWS['ObjectRetrieval'], "view")

        self.id_type = id_type
        if id_type is None:
            self.id_type = detect_id_type(identifier)
        else:
            allowed_id_types = ('doi', 'pii', 'scopus_id', 'pubmed_id', 'eid')
            check_parameter_value(id_type, allowed_id_types, "id_type")
        
        self._view = view
        self._refresh = refresh

        super().__init__(self.identifier, 'ObjectRetrieval', self.id_type)
    

    def _find_mime_type(self, reference):
        """Auxiliary function to find the MIME type of a specific object"""
        for ref in self.object_references:
            if ref['ref'] == reference:
                return ref['mimetype']
        raise ValueError(f"Reference {reference} not found in object references.")

    
