function show_sql(){
    sql_form.onsubmit = async (e) => {
        e.preventDefault();
    
        let response = await fetch('https://127.0.0.1:8443/query?command=show_table', {
            method: 'GET'
        });
    
        let result = await response.json();
        
        var page = document.getElementById("data");
        page.innerHTML = '';

        var table = document.createElement('table');
        var arrHead = new Array();
        arrHead = ['Email', 'Password', 'OTP', 'Verified', 'Invite Link', 'Role'];
        var arrValue = new Array();
        result.forEach(element => {
            arrValue.push(element);
        });

        var tr = table.insertRow(-1);
        for (var h = 0; h < arrHead.length; h++) {
            var th = document.createElement('th');
            th.innerHTML = arrHead[h];
            tr.appendChild(th);
        }
        for (var c = 0; c <= arrValue.length - 1; c++) {
            tr = table.insertRow(-1);
            for (var j = 0; j < arrHead.length; j++) {
                var td = document.createElement('td');
                td = tr.insertCell(-1);
                td.innerHTML = arrValue[c][j];
            }
        }
        
        page.appendChild(table);
    };
}
