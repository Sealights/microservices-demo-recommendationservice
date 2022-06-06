import pytest as pytest

from demo_pb2 import ListRecommendationsRequest, ListRecommendationsResponse, ListProductsResponse, Product
from demo_pb2_grpc import ProductCatalogServiceStub


@pytest.fixture(scope='module')
def grpc_add_to_server():
    from demo_pb2_grpc import add_RecommendationServiceServicer_to_server
    return add_RecommendationServiceServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer(module_mocker):
    from recommendation_server import RecommendationService
    mock_channel = module_mocker.patch("grpc.Channel", autospec=True)
    product_catalog_service = ProductCatalogServiceStub(mock_channel)
    response = ListProductsResponse(products=[
        Product(id="1"), Product(id="2"), Product(id="3"), Product(id="4")
    ])
    module_mocker.patch.object(product_catalog_service, "ListProducts").return_value = response
    return RecommendationService(product_catalog_service)


@pytest.fixture(scope='module')
def grpc_stub(grpc_channel):
    from demo_pb2_grpc import RecommendationServiceStub
    return RecommendationServiceStub(grpc_channel)


def test_ListRecommendations(grpc_stub):
    list_recommendations_request = ListRecommendationsRequest(product_ids=["1", "2"])
    response = grpc_stub.ListRecommendations(list_recommendations_request)

    assert isinstance(response, ListRecommendationsResponse)
    assert set(response.product_ids) == {"3", "4"}
    
