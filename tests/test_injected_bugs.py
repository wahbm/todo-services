import pytest
from tests.test_todos import client, create_todo
from app.test_faults import ACTIVE_BUGS


@pytest.mark.parametrize('bug_id', sorted(ACTIVE_BUGS))
def test_injected_bug(client, monkeypatch, bug_id):
    first = create_todo(client, 'Fault probe one')
    second = create_todo(client, 'Fault probe two')
    todo_id = first['id']
    if bug_id == 7:
        assert client.patch(f'/todos/{todo_id}/complete').json()['completed'] is True
    before = client.get(f'/todos/{todo_id}').json()
    monkeypatch.setattr('app.routes.todos.ACTIVE_BUGS', ACTIVE_BUGS)
    if bug_id == 1:
        a = client.get('/todos?page=1&page_size=1').json()
        b = client.get('/todos?page=2&page_size=1').json()
        assert len(a['items']) == 2
        assert a['items'] == b['items']
    elif bug_id == 2:
        assert client.request('DELETE', '/todos', json={'ids': [todo_id]}).status_code == 500
        assert len(client.get('/todos').json()['items']) == 2
        assert client.request('DELETE', '/todos', json={'ids': [todo_id, second['id']]}).json() == {'deleted': 2}
    elif bug_id == 3:
        r = client.get('/todos/stats/summary')
        assert r.status_code == 200
        assert r.json() == {'completed': 0, 'active': 2}
    elif bug_id == 4:
        r = client.get(f'/todos/{todo_id}')
        assert r.status_code == 200
        assert r.json() == {'id': todo_id}
    else:
        suffix = {5: '', 6: '/complete', 7: '/reopen'}[bug_id]
        r = client.patch(f'/todos/{todo_id}{suffix}', json={'title': 'Changed', 'completed': True})
        assert r.status_code == 200
        stored = next(x for x in client.get('/todos').json()['items'] if x['id'] == todo_id)
        assert stored == before
