// Recover existing grants omitted on an external navigation.
fetch('/session.js',{credentials:'same-origin',cache:'no-store'}).then(response=>{if(response.ok)location.replace('/');}).catch(()=>{});
