import typing
import logging
from influxdb_client.client.write_api import SYNCHRONOUS
from .db_base import DBBase, DMBSConfigBase, DBConfigBase
from influxdb_client import Point, WriteOptions
import ipdb


from  ..core import ObjMOSAIC

import pydantic
from influxdb_client import InfluxDBClient, Point
YNCHRONOUS = WriteOptions(batch_size=500, flush_interval=10_000, jitter_interval=2_000, retry_interval=5_000)





class InfluxDBConfig(DMBSConfigBase):  # 2. Adapter la classe de configuration de DB Base
    url: str = pydantic.Field(default="", description="URL of InfluxDB")
    org: str = pydantic.Field(default="", description="The Organization of InfluxDB")
    token: str = pydantic.Field(default="", description="InfluxDB authorization token")
    bucket: str = pydantic.Field(default="", description="Bucket to use in InfluxDB")

class DBInfluxDB(DBBase):
    config: InfluxDBConfig = pydantic.Field(default=InfluxDBConfig(), description="The InfluxDB configuration")

    def connect(self, **params):
        self.bkd = InfluxDBClient(url=self.config.url, token=self.config.token, org=self.config.org, **params)
        try:
            self.bkd.ping()
            if self.logger:
                self.logger.info("InfluxDB connected successfully")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to connect to InfluxDB: {str(e)}")
            return False

    def _resolve_bucket_measurement(self, endpoint):
        # 4. Mapper les concepts MOSAIC avec les concepts InfluxDB
        if self.name:
            bucket = self.name
            measurement = endpoint
        else:
            parts = endpoint.split('/')
            bucket = parts[0]
            measurement = parts[1] if len(parts) > 1 else None
        return bucket, measurement

  
    
    def put(self, endpoint, data=[], index=[], time_field="_time", **params):
        bucket, measurement = self._resolve_bucket_measurement(endpoint)

        points = []  # Pour stocker tous les points

        for item in data:
            point_measurement = item.get("measurement", measurement)
            point = Point(point_measurement)

        # Ajouter le timestamp s'il est présent dans la donnée
            if time_field in item:
                point.time(item[time_field])

            for idx in index:  # tags
                if idx in item and idx != time_field:
                    value = item[idx]
                    if not isinstance(value, (str, int, float)):
                        idx = str(value)
                    point.tag(idx, value)

        # Traiter chaque clé/valeur dans item comme un champ, 
        # sauf si c'est dans index, "measurement" ou "time_field"
            for key, value in item.items():
                if key not in index and key != "measurement" and key != time_field:
                    if not isinstance(value, (str, int, float)):
                        value = str(value)
                    point.field(key, value)

            points.append(point)  # Ajouter au tableau des points

        try:
            # Écrire tous les points en une seule fois
            with self.bkd.write_api(write_options=SYNCHRONOUS) as write_api:
                write_api.write(bucket=bucket, record=points)
            return {"success_count": len(data), "failure_count": 0}

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to put data in InfluxDB: {str(e)}")
            print(f"Erreur: {e}")  
            return {"success_count": 0, "failure_count": len(data)}





    def get(self, endpoint, filter={}, projection=[], limit=0, keep_influx_id=False, time_field="_time", **params):
        bucket, measurement = self._resolve_bucket_measurement(endpoint)

        if self.logger:
            self.logger.debug(f"Retrieving data from bucket: {bucket}, measurement: {measurement}")

        query = f'from(bucket: "{bucket}") |> range(start: 0)'
        if measurement:
            query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'

        filter_conditions = [f'r["{k}"] == "{v}"' for k, v in filter.items()]
        if filter_conditions:
            query += f' |> filter(fn: (r) => {" and ".join(filter_conditions)})'

        if projection:
            fields_filter = ' or '.join([f'r._field == "{field}"' for field in projection])
            query += f' |> filter(fn: (r) => {fields_filter})'

        if limit > 0:
            query += f' |> limit(n: {limit})'

        if self.logger:
            self.logger.debug(f"Constructed InfluxDB Query: {query}")

        try:
            result = self.bkd.query_api().query(query)
            data = []
            for table in result:
                for record in table.records:
                    item = record.values
                    if not keep_influx_id:
                        item.pop(time_field, None)
                # Keep _value as it is significant data
                # if projection:
                #     item = {key: item[key] for key in projection if key in item}
                    data.append(item)

            if self.logger:
                self.logger.info(f"Retrieved {len(data)} records from InfluxDB.")
            return data
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to retrieve data from InfluxDB: {str(e)}")
            return []


        


    def update(self, endpoint, time_field, tags, fields):
        # Formatage correct du timestamp pour InfluxDB
        formatted_timestamp = time_field.strftime('%Y-%m-%dT%H:%M:%SZ')  # Format ISO 8601

        # Construit la nouvelle donnée avec les champs mis à jour
        data_to_update = []

        # Créez un nouveau point avec les tags et les champs mis à jour
        new_point = {
            "measurement": endpoint.split('/')[-1],  
            "time_field": formatted_timestamp,
            **tags,  # Tags existants à conserver
            **fields  # Nouveaux champs à mettre à jour
        }

    # Ajoute la nouvelle pointe à la liste des données à mettre à jour
        data_to_update.append(new_point)

    # Appelle la méthode put pour écrire la mise à jour dans InfluxDB
        result = self.put(endpoint=endpoint, data=data_to_update)

    # Vous pouvez vérifier le résultat et agir en conséquence
        if result['failure_count'] > 0:
            if self.logger:
                self.logger.error(f"Failed to update data in InfluxDB: {result}")
            return False 
        else:
            if self.logger:
                self.logger.info(f"Data updated in InfluxDB: {result}")
            return True 





    def reset(self, endpoint):
        bucket, measurement = self._resolve_bucket_measurement(endpoint)

    # Suppression du bucket
        buckets_api = self.bkd.buckets_api()
        bucket_obj = next((b for b in buckets_api.find_buckets() if b.name == bucket), None)
        if bucket_obj:
            try:
                buckets_api.delete_bucket(bucket_id=bucket_obj.id)
                if self.logger:
                    self.logger.info(f"Deleted bucket '{bucket}'.")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to delete bucket: {e}")

    # Recréation du bucket
        try:
            buckets_api.create_bucket(bucket_name=bucket)
            if self.logger:
                self.logger.info(f"Recreated bucket '{bucket}'.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to recreate bucket: {e}")

    def size(self, endpoint):
        bucket, measurement = self._resolve_bucket_measurement(endpoint)
    
        query = f'from(bucket: "{bucket}") |> range(start: -1y) |> filter(fn: (r) => r["_measurement"] == "{measurement}") |> count(column: "_value")'
        tables = self.bkd.query_api().query(query, org=self.config.org)
    
        count = 0
        for table in tables:
            for record in table.records:
                count += record.get_value()
    
        return count


    def delete(self, endpoint, start_timestamp, stop_timestamp, tags):
        bucket, measurement = self._resolve_bucket_measurement(endpoint)
    
        delete_predicate = f'_measurement="{measurement}"'
        for tag_key, tag_value in tags.items():
            delete_predicate += f' AND {tag_key}="{tag_value}"'
        
        try:
            formatted_start = start_timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            formatted_stop = stop_timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            self.bkd.delete_api().delete(start=formatted_start, stop=formatted_stop, predicate=delete_predicate, bucket=bucket, org=self.config.org)
            if self.logger:
                self.logger.info(f"Deleted data in bucket '{bucket}' between '{formatted_start}' and '{formatted_stop}' with predicate '{delete_predicate}'.")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to delete data: {e}")
            return False
        
    def close(self):
        if hasattr(self, 'bkd') and self.bkd:
            self.bkd.__del__()
            if self.logger:
                self.logger.info("InfluxDB connection closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


 
