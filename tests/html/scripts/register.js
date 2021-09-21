function send_form() {
    register_form.onsubmit = async (e) => {
        e.preventDefault();
        if(document.getElementById("otp").value.match(/^[0-9]{1,6}$/) != null){
            var query = 'https://0.0.0.0:8443/register?email=' 
                + document.getElementById("email").value.replace("@", "%40") + "&pwd="
                + document.getElementById("pwd").value + "&otp="
                + document.getElementById("otp").value

            let response = await fetch(query, {
                method: 'GET'
            });
            let result = await response.text();
            alert(result);
            return
        }
    
        alert("OTP format not matched.");
    };
}

function send_otp(){
    register_form.onsubmit = async (e) => {
        e.preventDefault();
    
        let response = await fetch('https://0.0.0.0:8443/otp?email=' + document.getElementById("email").value.replace("@", "%40"), {
            method: 'GET'
        });
    
        let result = await response.text();
    
        alert(result);
    };
}
