from flask import Flask, render_template, request, jsonify
import json
from ai_engine import run_decision
from database import db
from logger import get_logger

logger = get_logger()

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    """Render decision interface."""
    result = None
    error = None
    decision_id = None
    
    if request.method == "POST":
        situation = request.form.get("situation", "").strip()
        sop = request.form.get("sop", "").strip()
        
        if not situation:
            error = "Situation cannot be empty"
        else:
            # Generate decision
            logger.info(f"Processing decision request")
            response = run_decision(situation, sop)
            
            if response["success"]:
                result = response["data"]
                
                # Save to database
                decision_id = db.save_decision(situation, result, sop)
                logger.info(f"Decision saved to database - ID: {decision_id}")
            else:
                error = response["error"]
    
    return render_template("index.html", result=result, error=error, decision_id=decision_id)


@app.route("/api/decision", methods=["POST"])
def api_decision():
    """API endpoint for generating decisions."""
    try:
        data = request.get_json()
        
        if not data or "situation" not in data:
            return jsonify({"success": False, "error": "Missing 'situation' field"}), 400
        
        situation = data.get("situation", "").strip()
        sop = data.get("sop", "").strip()
        
        if not situation:
            return jsonify({"success": False, "error": "Situation cannot be empty"}), 400
        
        # Generate decision
        response = run_decision(situation, sop)
        
        if response["success"]:
            # Save to database
            decision_id = db.save_decision(situation, response["data"], sop)
            
            return jsonify({
                "success": True,
                "decision_id": decision_id,
                "data": response["data"]
            })
        else:
            return jsonify({
                "success": False,
                "error": response["error"]
            }), 500
    
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def api_history():
    """Retrieve decision history."""
    try:
        limit = request.args.get("limit", 10, type=int)
        decisions = db.get_recent_decisions(limit=limit)
        
        return jsonify({
            "success": True,
            "count": len(decisions),
            "data": decisions
        })
    
    except Exception as e:
        logger.error(f"History API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/decision/<int:decision_id>", methods=["GET"])
def api_get_decision(decision_id):
    """Retrieve a specific decision."""
    try:
        decision = db.get_decision(decision_id)
        
        if not decision:
            return jsonify({"success": False, "error": "Decision not found"}), 404
        
        return jsonify({
            "success": True,
            "data": decision
        })
    
    except Exception as e:
        logger.error(f"Get decision error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Get decision statistics."""
    try:
        stats = db.get_statistics()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting DIOS application")
    app.run(host="0.0.0.0", port=5000, debug=False)
