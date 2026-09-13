from ml.utils.geometry import bbox_center, point_in_polygon, euclidean_distance, max_displacement


def test_bbox_center():
    assert bbox_center((0, 0, 10, 10)) == (5.0, 5.0)


def test_point_in_polygon_inside():
    polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert point_in_polygon((5, 5), polygon) is True


def test_point_in_polygon_outside():
    polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert point_in_polygon((15, 5), polygon) is False


def test_euclidean_distance():
    assert euclidean_distance((0, 0), (3, 4)) == 5.0


def test_max_displacement():
    points = [(0, 0), (1, 1), (5, 5)]
    assert max_displacement(points) == euclidean_distance((0, 0), (5, 5))