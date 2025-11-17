# API Testing Guide - Before Deploying to Raspberry Pi

This guide will help you verify that your API is working correctly before deploying to your Raspberry Pi.

## Quick Start

### 1. Start the API Server Locally

```bash
# Make sure you're in the project directory
cd /Volumes/SHGP31-5/code/mobis_dash_panel

# Start the server
python3 app.py
```

The server should start on `http://localhost:8050`

### 2. Run Automated Tests

```bash
# In a new terminal, run the test script
python3 test_api.py
```

This will test all API endpoints automatically.

### 3. Manual Testing with curl

You can also test endpoints manually using curl:

#### Health Check
```bash
curl http://localhost:8050/api/health
```

#### Search All Tests
```bash
curl http://localhost:8050/api/search/tests
```

#### Search with Filters
```bash
# Search by subject
curl "http://localhost:8050/api/search/tests?subject=SubjectName"

# Search by scenario
curl "http://localhost:8050/api/search/tests?scenario=ScenarioName"

# Combined search
curl "http://localhost:8050/api/search/tests?subject=SubjectName&scenario=ScenarioName"
```

#### Get Test Details
```bash
# Replace 1 with an actual test_id from your database
curl http://localhost:8050/api/tests/1/paths
curl http://localhost:8050/api/tests/1/sensors
```

#### Optimization Parameters
```bash
# Search all optimization parameters
curl http://localhost:8050/api/optimization/parameters

# Search with filters
curl "http://localhost:8050/api/optimization/parameters?subject_id=SUBJECT_001&scenario=ScenarioName"

# Get parameter detail (replace 1 with actual parameter_id)
curl http://localhost:8050/api/optimization/parameters/1
```

## Testing Checklist

Before deploying to Raspberry Pi, verify:

### ✅ Basic Functionality
- [ ] API health endpoint responds (`/api/health`)
- [ ] All endpoints return valid JSON
- [ ] No 500 errors in logs

### ✅ Test Search Endpoints
- [ ] `/api/search/tests` returns data
- [ ] Filtering by subject works
- [ ] Filtering by scenario works
- [ ] Filtering by sensor_id works
- [ ] Combined filters work

### ✅ Test Detail Endpoints
- [ ] `/api/tests/<id>/paths` returns correct paths
- [ ] `/api/tests/<id>/sensors` returns sensor list
- [ ] 404 errors work correctly for invalid IDs

### ✅ Optimization Endpoints
- [ ] `/api/optimization/parameters` returns data
- [ ] Filtering optimization parameters works
- [ ] `/api/optimization/parameters/<id>` returns detail
- [ ] File serving works (`/api/optimization/files/<path>`)
- [ ] Invalid strategy number returns 400 error

### ✅ Error Handling
- [ ] Invalid endpoints return 404
- [ ] Invalid test_id returns 404
- [ ] Invalid parameter_id returns 404
- [ ] Security: files outside workspace return 403

### ✅ Performance
- [ ] API responds within reasonable time (< 2 seconds)
- [ ] Database queries are optimized
- [ ] No memory leaks during extended use

## Testing from Another Machine

If you want to test from another machine on your network:

1. **Find your local IP address:**
   ```bash
   # On Mac/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # On Windows
   ipconfig
   ```

2. **Start server with network access:**
   ```bash
   # The app.py already uses host='0.0.0.0' which allows network access
   python3 app.py
   ```

3. **Test from another machine:**
   ```bash
   # Replace YOUR_IP with your actual IP address
   python3 test_api.py http://YOUR_IP:8050
   ```

## Testing on Raspberry Pi (Before Full Deployment)

### Option 1: Test Remotely

1. **Copy files to Pi:**
   ```bash
   # From your development machine
   scp -r /Volumes/SHGP31-5/code/mobis_dash_panel pi@raspberrypi.local:/home/pi/mobis_dash_panel
   ```

2. **SSH into Pi:**
   ```bash
   ssh pi@raspberrypi.local
   ```

3. **Install dependencies:**
   ```bash
   cd /home/pi/mobis_dash_panel
   pip3 install -r requirements.txt
   ```

4. **Run tests:**
   ```bash
   # Start server in one terminal
   python3 app.py
   
   # In another terminal (or from your dev machine)
   python3 test_api.py http://raspberrypi.local:8050
   ```

### Option 2: Test Locally on Pi

1. **SSH into Pi and run:**
   ```bash
   cd /home/pi/mobis_dash_panel
   python3 app.py
   ```

2. **From Pi's browser, test:**
   - `http://localhost:8050/api/health`
   - `http://localhost:8050/api/search/tests`

## Common Issues and Solutions

### Issue: Connection Refused
**Solution:** Make sure the server is running and listening on the correct port.

### Issue: Database Errors
**Solution:** 
- Check that `db/imu_data.db` exists
- Verify database permissions
- Run database indexing: The app does this automatically on startup

### Issue: File Not Found (404)
**Solution:**
- Verify file paths in database
- Check that data files exist in expected locations
- Verify workspace root path is correct

### Issue: Permission Denied (403)
**Solution:**
- Check file permissions
- Verify workspace root configuration
- Ensure files are within the workspace directory

### Issue: Slow Response Times
**Solution:**
- Check database indexing status
- Verify data file sizes aren't too large
- Consider adding database indexes for frequently queried fields

## Production Deployment Checklist

Before deploying to production on Pi:

- [ ] All tests pass
- [ ] Error handling works correctly
- [ ] Security checks are in place (403 for unauthorized file access)
- [ ] Database is properly indexed
- [ ] File paths are correct for Pi environment
- [ ] Dependencies are installed
- [ ] Server starts automatically on boot (if needed)
- [ ] Firewall rules allow port 8050 (if applicable)
- [ ] Logs are being written correctly

## Using Postman or Similar Tools

You can also use Postman, Insomnia, or similar API testing tools:

1. **Import these endpoints:**
   - `GET http://localhost:8050/api/health`
   - `GET http://localhost:8050/api/search/tests`
   - `GET http://localhost:8050/api/tests/{id}/paths`
   - `GET http://localhost:8050/api/optimization/parameters`

2. **Create a collection** with all endpoints
3. **Run the collection** to test all endpoints at once

## Monitoring and Logs

Watch the server logs while testing:
- Look for any error messages
- Check response times
- Monitor database query performance
- Watch for any exceptions

## Next Steps After Testing

Once all tests pass:

1. **Deploy to Pi** with confidence
2. **Set up auto-start** if needed (systemd service)
3. **Configure firewall** if required
4. **Set up monitoring** for production use
5. **Document any Pi-specific configurations**

---

**Remember:** Always test thoroughly before deploying to production! 🚀

