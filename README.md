$capacity = Invoke-RestMethod http://127.0.0.1:8000/api/system/flows

$capacity | Select-Object `
    total_capacity,
    headless_capacity,
    online_capacity,
    active_headless,
    headed_capacity,
    online_headed_capacity,
    active_headed
