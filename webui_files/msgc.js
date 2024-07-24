function removeSomeMessage(uuids)
{
	param = JSON.stringify({"uuids": uuids})
	fr22BackendPost('/api/builtin/msgcenter/remove', JSON.stringify(param))
		.done(function() {
			// fr22ShowToast('success', " completed");
			setTimeout($("#msgCenterList").DataTable().ajax.reload, 200);
		});
}

function touchAllMessages(uuids)
{
	let param = JSON.stringify({'uuids': uuids});
	fr22BackendPost('/api/builtin/msgcenter/update', param)
		.done(function() {
			// fr22ShowToast('success', " completed");
			setTimeout($("#msgCenterList").DataTable().ajax.reload, 200);
		});
}

function executeApiAction(api, params)
{
	if (api && params)
		window.alert(api);

	fr22BackendPost(api, params)
		.done(function() {
			fr22ShowToast('success', " completed");
			setTimeout($("#msgCenterList").DataTable().ajax.reload, 200);
		});
}

function getActions(db)
{
	let line;
	const uuid = db['uuid'];
	const action = db['action'];
	const on_remove = 'title="Remove" onclick=removeSomeMessage(["' + uuid + '"])';
	line = '<div class="appActions">';
	line += '<i class="fas fa-trash-alt" ' + on_remove + '></i>';
	if (action && action.api && action.params) {
		const api = '"' + action.api.toString() + '"';
		const params = '"' + action.params.toString() + '"';
		let on_api_request = 'title="Action" ';
		on_api_request += 'onclick=executeApiAction(' + api + ',' + params + ')';
		line += '<i class="fas fa-sync text-info" ' + on_api_request + '></i>';
	}
	line += '</div>';
	return line;
}

function readAllMessages()
{
	fr22BackendGet("/api/builtin/msgcenter/get")
		.done(function(json) {
			let data = [];
			json["data"].forEach(i => {
				data.push(i["uuid"]);
			});
			touchAllMessages(data);
		});
}

function clearAllMessages()
{
	fr22BackendGet("/api/builtin/msgcenter/get")
		.done(function(json) {
			let data = [];
			json["data"].forEach(i => {
				data.push(i["uuid"]);
			});
			removeSomeMessage(data);
		});
}

$(document).ready(function() {
	$('#msgCenterList').DataTable({
		ajax: {
			url: fr22Address('/api/builtin/msgcenter/get'),
			dataSrc: function(json) {
				let a = [];
				json["data"].forEach(i => {
					i["actions"] = getActions(i);
					a.push(i);
					// console.log("forEach:", i);
				});
				return a;
			}
		},
		columns: [
			{ data: 'level', className: "text-right", render: function (data, type, row){
					let icon = '';
					if(data === 'warning'){
						icon = '-circle';
					}
					else if(data === 'error'){
						icon = '-triangle';
					}
					return '<i class="fas fa-exclamation'+ icon +'"></i>';
				} 
			},
			{ data: 'stamp', render:
				function (data, type, row) {
					const date = new Date(Number(data) * 1000);
					const stamp = date.toLocaleString('fi-FI');
					return stamp;
				}
			},
			{ data: 'msg', render:
				function (data, type, row) {
					let msg = data
					if (row.state === 1)
						return msg.bold();
					else
						return msg;
				}
			},
			{ data: 'actions' },
		],
		columnDefs: [
			{ "width": "10%", "targets": 0 },
			{ "width": "3%", "targets": 1 },
			{ "width": "3%", "targets": 3 },
			{ "type": "date-eu", "targets": 1 }
		],
		order: [1, 'desc'],
		paging: true,
		ordering: true,
		searching: false,
		info: false
	});

	$("#clearMessages").click(function () {
		clearAllMessages();
		fr22ShowToast('success', 'Message list cleared!');
		setTimeout($("#msgCenterList").DataTable().ajax.reload, 200);
	});
	readAllMessages();
});
