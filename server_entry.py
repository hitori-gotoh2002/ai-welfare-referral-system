import backend_runtime_patch
import recommendation_relevance_patch
import backend_server


backend_runtime_patch.apply()
recommendation_relevance_patch.apply()


if __name__ == "__main__":
    backend_server.run()
