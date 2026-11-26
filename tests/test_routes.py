from app import app

client = app.test_client()

# テスト①：トップページ
response = client.get("/")

assert response.status_code == 200
print("テスト① 成功")


# テスト②：キーワード検索
# ヒント：client.get("/?q=Python")
response = client.get("/?q=Python")

assert response.status_code == 200
print("テスト② 成功")

# テスト③：古い順の並べ替え
response = client.get("/?sort=old")

assert response.status_code == 200
print("テスト③ 成功")

# テスト④：キーワード検索 + タイトル順
response = client.get("/?q=Python&sort=title")

assert response.status_code == 200
print("テスト④ 成功")

# テスト⑤：存在しないURL
# ヒント：今回は404が正解
response = client.get("/ayuserver")

assert response.status_code == 404
print("テスト⑤ 成功")

print("すべてのテストが完了しました！")
