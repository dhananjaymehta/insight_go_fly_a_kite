# <----------------------------STREAM INDEX SCHEMA------------------------->
curl -u elastic -XPUT 'localhost:9200/stream_data' -d ' 
{"mappings":  
        { "data" :
              { "_all" : { "enabled" : false},
              	"properties" :  
                      {
                        "location" : {
                              "type" : "geo_point",
                              "doc_values" : false
                                    },
                        "wind" : {
                              "type" : "integer",
                              "index" : "not_analyzed"
                                    },
                        "year" : {
                              "type" : "string",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        },
                        "month" : {
                              "type" : "string",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        },
                        "day" : {
                              "type" : "string",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        },
                        "time" : {
                              "type" : "string",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        },
                        "hour" : {
                            "type": "string",
                            "index" : "not_analyzed",
                            "doc_values" : false
                        },
                        "min" : {
                              "type" : "string",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        }  
                      }
              }
        }
}'
# <-------------------------------------circles schema--------------------------------------------------->
curl -u elastic -XPUT 'localhost:9200/circles' -d ' 
{"mappings":  
        { "data" :
              { "_all" : { "enabled" : false},
                "properties" :  {
                        "shape" : {
                            "type" : "string",
                            "index" : "not_analyzed",
                            "doc_values": false
                        },
                       "lists" : { 
                             "properties" : {
                                  "season" : {
                                      "type" : "float",
                                      "index" : "not_analyzed",
                                      "doc_values": false
                                  }
                         }
                     }
                    }
              }
        }
}'
# <------------------------------------BATCH INDEX SCHEMA-------------------------------------------------->
curl -u elastic -XPUT 'localhost:9200/batch_data' -d ' 
{"mappings":  
        { "data" :
              { "_all" : { "enabled" : false},
              	"properties" :  
                      {
                        "location" : {
                              "type" : "geo_point",
                              "doc_values" : false
                                    },
                        "year" : {
                              "type" : "string",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        },
                        "month" : {
                              "type" : "string",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        },
                        "day" : {
                              "type" : "string",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        },
                        "maxWs" : {
                              "type" : "integer",
                              "index" : "not_analyzed",
                              "doc_values" : false
                        },
                        "lists" : { 
                                   "properties" : {
                                        "times" : {
                                            "type" : "string",
                                            "index" : "not_analyzed",
                                            "doc_values": false
                                        },
                                        "winds" : {
                                            "type" : "integer",
                                            "index" : "not_analyzed",
                                            "doc_values": false
                                        }
                                }
                        }
                    }
               }
        }
}'
# <--------------------------------FORMATTED-------------------------->
curl -u elastic -XPUT 'localhost:9200/batch_data' -d ' 
{"mappings":  {"data": {"_all": {"enabled": false}, "properties": {"location": {"type": "geo_point", "doc_values": false}, "year": {"type": "string", "index": "not_analyzed", "doc_values": false}, "month": {"type": "string", "index": "not_analyzed", "doc_values": false},"day" : { "type" : "string","index" : "not_analyzed", "doc_values" : false},"maxWs" : {"type" : "integer","index" : "not_analyzed","doc_values" : false},"lists" : { "type" : {"properties" : {"times" : {"type" : "string"},"winds" : {"type" : "integer"}}}}}}}}'







































