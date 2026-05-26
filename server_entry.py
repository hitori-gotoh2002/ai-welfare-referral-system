import backend_runtime_patch
import recommendation_relevance_patch
import detail_alias_patch
import llm_enhancement_patch
import rich_report_patch
import welfare_link_patch
import welfare_feature_patch
import commercial_ui_route_patch
import detail_source_patch
import backend_server


backend_runtime_patch.apply()
recommendation_relevance_patch.apply()
detail_alias_patch.apply()
llm_enhancement_patch.apply()
rich_report_patch.apply()
welfare_link_patch.apply()
welfare_feature_patch.apply()
commercial_ui_route_patch.apply()
detail_source_patch.apply()


if __name__ == "__main__":
    backend_server.run()
