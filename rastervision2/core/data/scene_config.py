from typing import Optional, List

from shapely.geometry import shape

from rastervision2.pipeline.config import Config, register_config
from rastervision2.core.data.raster_source import RasterSourceConfig
from rastervision2.core.data.label_source import LabelSourceConfig
from rastervision2.core.data.label_store import LabelStoreConfig
from rastervision2.core.data.scene import Scene
from rastervision2.core.data.vector_source import GeoJSONVectorSourceConfig


@register_config('scene')
class SceneConfig(Config):
    id: str
    raster_source: RasterSourceConfig
    label_source: LabelSourceConfig
    label_store: Optional[LabelStoreConfig] = None
    aoi_uris: Optional[List[str]] = None

    def build(self, class_config, tmp_dir):
        raster_source = self.raster_source.build(tmp_dir)
        crs_transformer = raster_source.get_crs_transformer()
        extent = raster_source.get_extent()

        label_source = (
            self.label_source.build(class_config, crs_transformer, extent)
            if self.label_source is not None else None)
        label_store = (
            self.label_store.build(class_config, crs_transformer)
            if self.label_store is not None else None)

        aoi_polygons = None
        if self.aoi_uris is not None:
            aoi_polygons = []
            for uri in self.aoi_uris:
                aoi_geojson = GeoJSONVectorSourceConfig(uri=uri).build(
                    class_config, crs_transformer).get_geojson()
                for f in aoi_geojson['features']:
                    aoi_polygons.append(shape(f['geometry']))

        return Scene(
            self.id,
            raster_source,
            ground_truth_label_source=label_source,
            prediction_label_store=label_store,
            aoi_polygons=aoi_polygons)

    def update(self, pipeline=None):
        super().update()

        self.raster_source.update(pipeline=pipeline, scene=self)
        self.label_source.update(pipeline=pipeline, scene=self)
        if self.label_store is None and pipeline is not None:
            self.label_store = pipeline.get_default_label_store(scene=self)
        if self.label_store is not None:
            self.label_store.update(pipeline=pipeline, scene=self)
