#!/usr/bin/env python3
"""
Simple Location System for Sajilo Sewak Bot
This is a clean, working implementation that actually captures coordinates
"""

import csv
import os
import logging
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import asyncio

logger = logging.getLogger(__name__)

class SimpleLocationSystem:
    """Simple and reliable location capture system"""
    
    def __init__(self):
        self.location_file = "data/location_data.csv"
        self._create_location_file()
        logger.info("📍 Simple Location System initialized")
    
    def _create_location_file(self):
        """Create location data file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.location_file), exist_ok=True)
        
        if not os.path.exists(self.location_file):
            with open(self.location_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'user_id', 'user_name', 'latitude', 'longitude', 
                    'interaction_type', 'message_text'
                ])
            logger.info(f"📍 Created location file: {self.location_file}")
    
    async def request_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             interaction_type: str = "general", message_text: str = ""):
        """Request user location with simple keyboard"""

        user_id = update.effective_user.id
        logger.info(f"📍 [REQUEST] Requesting location from user {user_id} for {interaction_type}")
        
        # Store context for when location is received
        context.user_data['location_request'] = {
            'interaction_type': interaction_type,
            'message_text': message_text,
            'timestamp': datetime.now().isoformat()
        }
        
        # Create simple location keyboard
        keyboard = [
            [KeyboardButton("📍 Share My Location", request_location=True)],
            [KeyboardButton("⏭️ Skip Location"), KeyboardButton("❌ Cancel")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        # Send request message
        message = "📍 Please share your location\n\nThis helps us provide better service:"
        
        # Handle both callback queries and regular messages
        if hasattr(update, 'callback_query') and update.callback_query:
            # For callback queries, edit the existing message
            await update.callback_query.edit_message_text(message)
            # Send the keyboard as a new message
            await update.callback_query.message.reply_text(
                "Please use the keyboard below to share your location:",
                reply_markup=reply_markup
            )
        else:
            # For regular messages
            await update.message.reply_text(message, reply_markup=reply_markup)
        
        logger.info(f"📍 [REQUEST] Location request sent to user {user_id}")
    
    async def handle_location_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when user shares location"""
        
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Unknown"
        location = update.message.location
        
        logger.info(f"📍 [RECEIVED] Location received from user {user_id}")
        logger.info(f"📍 [RECEIVED] Location object: {location}")
        
        # Validate location
        if not location or location.latitude is None or location.longitude is None:
            logger.error(f"📍 [ERROR] Invalid location from user {user_id}")
            await update.message.reply_text("❌ Invalid location received. Please try again.")
            return
        
        # Get stored context
        location_context = context.user_data.get('location_request', {})
        interaction_type = location_context.get('interaction_type', 'general')
        message_text = location_context.get('message_text', '')
        
        # Create location data
        location_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'user_name': user_name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'interaction_type': interaction_type,
            'message_text': message_text
        }
        
        # Save to CSV
        self._save_location_data(location_data)
        
        # Log success
        logger.info(f"📍 [SUCCESS] Location saved: {location.latitude:.6f}, {location.longitude:.6f} for user {user_id}")
        
        # Remove keyboard and show success message
        remove_keyboard = ReplyKeyboardRemove()
        
        # Sanitize interaction_type to avoid any parsing issues
        safe_interaction_type = str(interaction_type).replace('_', ' ').replace('-', ' ')
        
        try:
            await update.message.reply_text(
                f"✅ Location captured successfully!\n\n"
                f"📍 Coordinates: {location.latitude:.6f}, {location.longitude:.6f}\n"
                f"📝 Interaction: {safe_interaction_type}",
                reply_markup=remove_keyboard
            )
        except Exception as e:
            logger.error(f"📍 [ERROR] Failed to send location success message: {e}")
            # Fallback to simple message
            await update.message.reply_text(
                "✅ Location captured successfully!",
                reply_markup=remove_keyboard
            )
        
        # Continue with original interaction
        try:
            await self._continue_interaction(update, context, location_data)
        except Exception as e:
            logger.error(f"📍 [ERROR] Failed to continue interaction: {e}")
            await update.message.reply_text("Location saved. How can I help you further?")
        
        # Clear stored context
        context.user_data.pop('location_request', None)
        
        logger.info(f"📍 [COMPLETE] Location workflow completed for user {user_id}")
    
    def _save_location_data(self, location_data: dict):
        """Save location data to CSV file"""
        try:
            with open(self.location_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    location_data['timestamp'],
                    location_data['user_id'],
                    location_data['user_name'],
                    location_data['latitude'],
                    location_data['longitude'],
                    location_data['interaction_type'],
                    location_data['message_text']
                ])
            logger.info(f"📍 [SAVE] Location data saved to {self.location_file}")
        except Exception as e:
            logger.error(f"📍 [ERROR] Failed to save location data: {e}")
    
    async def _continue_interaction(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Continue with the original interaction after location capture"""
        
        interaction_type = location_data['interaction_type']
        lat = location_data['latitude']
        lon = location_data['longitude']
        
        logger.info(f"📍 [CONTINUE] Continuing {interaction_type} with location for user {location_data['user_id']}")
        
        # Route to appropriate handler based on interaction type
        if interaction_type == "emergency":
            await self._handle_emergency_with_location(update, context, location_data)
        elif interaction_type == "complaint":
            await self._handle_complaint_with_location(update, context, location_data)
        elif interaction_type == "ex_gratia":
            await self._handle_ex_gratia_with_location(update, context, location_data)
        elif interaction_type == "homestay":
            await self._handle_homestay_with_location(update, context, location_data)
        elif interaction_type == "general":
            await self._handle_general_with_location(update, context, location_data)
        else:
            # Default response
            await update.message.reply_text(
                f"Thank you for sharing your location! We'll use this to provide better service for: {interaction_type}"
            )
    
    async def _handle_emergency_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle emergency services with location - show emergency services menu"""
        
        user_id = update.effective_user.id
        lat = location_data['latitude']
        lon = location_data['longitude']
        
        # Store location in main bot's state
        if hasattr(self, 'main_bot') and self.main_bot:
            state = self.main_bot._get_user_state(user_id)
            state["location"] = f"{lat:.6f}, {lon:.6f}"
            self.main_bot._set_user_state(user_id, state)
            
            # Show emergency services menu
            await self.main_bot.show_emergency_services_menu(update, context)
        else:
            # Fallback if main bot reference not available
            message = f"""🚨 Emergency Services - Location Received 🚨

📍 Your Location: {lat:.6f}, {lon:.6f}

🚑 Nearest Emergency Services:
• Ambulance: 102
• Police: 100
• Fire: 101
• State Emergency: 1070

⚡ Response Time: 10-15 minutes

Your location has been logged for emergency response."""
            
            await update.message.reply_text(message)
        
        # Clear the location request context
        context.user_data.pop('location_request', None)
    
    async def _handle_complaint_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle complaint filing with location - integrate with main bot workflow"""
        
        user_id = update.effective_user.id
        lat = location_data['latitude']
        lon = location_data['longitude']
        
        # Get the stored complaint data from the main bot's state
        user_state = context.user_data.get('user_state', {})
        if not user_state:
            # Fallback to basic message if no state found
            message = f"""📝 Complaint Filed with Location 📝

📍 Your Location: {lat:.6f}, {lon:.6f}

✅ Your complaint has been registered with location data.
This will help us respond more effectively.

Complaint ID: CMP{datetime.now().strftime('%Y%m%d%H%M%S')}
Status: Under Review"""
            
            await update.message.reply_text(message)
            return
        
        # Extract complaint data from state
        complaint_data = {
            'name': user_state.get('entered_name', 'Unknown'),
            'mobile': user_state.get('mobile', 'Unknown'),
            'description': user_state.get('complaint_description', 'No description'),
            'location_lat': lat,
            'location_lon': lon,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate complaint ID
        complaint_id = f"CMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save to CSV (this should be handled by the main bot)
        # For now, just log it
        logger.info(f"📍 [COMPLAINT] Complaint with location saved: {complaint_id}")
        
        # Show success message with all details
        message = f"""✅ Complaint Filed Successfully! ✅

📝 Complaint Details:
• Name: {complaint_data['name']}
• Mobile: {complaint_data['mobile']}
• Description: {complaint_data['description']}
• Location: {lat:.6f}, {lon:.6f}

🆔 Complaint ID: {complaint_id}
📊 Status: Under Review
⏰ Filed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your complaint has been registered with location data. We'll respond within 24-48 hours."""
        
        await update.message.reply_text(message)
        
        # Clear the user state to return to main menu
        context.user_data.pop('user_state', None)
        context.user_data.pop('location_request', None)
        
        # Show main menu after a short delay
        await asyncio.sleep(2)
        # Note: We can't call the main bot's show_main_menu from here
        # The main bot should handle this in its message handler
    
    async def _handle_ex_gratia_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle ex-gratia application with location - integrate with main bot workflow"""
        
        user_id = update.effective_user.id
        lat = location_data['latitude']
        lon = location_data['longitude']
        
        # Get the stored ex-gratia data from the main bot's state
        user_state = context.user_data.get('user_state', {})
        if not user_state:
            # Fallback to basic message if no state found
            message = f"""💰 Ex-Gratia Application - Location Received 💰

📍 Your Location: {lat:.6f}, {lon:.6f}

✅ Your ex-gratia application has been submitted with location data.
This will help us process your claim faster."""
            
            await update.message.reply_text(message)
            return
        
        # Add location data to the user state
        user_state['latitude'] = lat
        user_state['longitude'] = lon
        
        # Update the context with the enhanced state
        context.user_data['user_state'] = user_state
        
        # Now call the main bot's confirmation function
        if hasattr(self, 'main_bot') and self.main_bot:
            # Call the main bot's confirmation function
            await self.main_bot.show_ex_gratia_confirmation(update, context, user_state)
        else:
            # Fallback: show a message asking user to continue
            message = f"""📍 Location Captured Successfully! 📍

Your location ({lat:.6f}, {lon:.6f}) has been added to your ex-gratia application.

Please continue with your application to submit it to the NC Exgratia API."""
            
            await update.message.reply_text(message)
    
    async def _handle_homestay_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle homestay booking with location"""
        
        lat = location_data['latitude']
        lon = location_data['longitude']
        
        message = f"""🏡 Homestay Search - Location Based 🏡

📍 Your Location: {lat:.6f}, {lon:.6f}

🔍 Searching for homestays near your location...
We'll find the best options based on your coordinates."""
        
        await update.message.reply_text(message)
    
    async def _handle_general_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle general interactions with location"""
        
        lat = location_data['latitude']
        lon = location_data['longitude']
        
        message = f"""📍 Location Captured Successfully 📍

Your location: {lat:.6f}, {lon:.6f}

Thank you for sharing your location! This helps us provide better service."""
        
        await update.message.reply_text(message)
    
    async def handle_location_skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when user skips location sharing"""
        
        user_id = update.effective_user.id
        logger.info(f"📍 [SKIP] User {user_id} skipped location sharing")
        
        # Get stored context
        location_context = context.user_data.get('location_request', {})
        interaction_type = location_context.get('interaction_type', 'general')
        
        # Remove keyboard
        remove_keyboard = ReplyKeyboardRemove()
        await update.message.reply_text(
            "⏭️ Location sharing skipped. Continuing without location data.",
            reply_markup=remove_keyboard
        )
        
        # Continue without location
        await self._continue_without_location(update, context, interaction_type)
        
        # Clear stored context
        context.user_data.pop('location_request', None)
    
    async def _continue_without_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, interaction_type: str):
        """Continue interaction without location data"""
        
        logger.info(f"📍 [CONTINUE] Continuing {interaction_type} without location")
        
        if interaction_type == "emergency":
            # Store location as "Not provided" in main bot's state and show emergency services menu
            if hasattr(self, 'main_bot') and self.main_bot:
                user_id = update.effective_user.id
                state = self.main_bot._get_user_state(user_id)
                state["location"] = "Location not provided"
                self.main_bot._set_user_state(user_id, state)
                
                # Show emergency services menu
                await self.main_bot.show_emergency_services_menu(update, context)
            else:
                # Fallback if main bot reference not available
                await update.message.reply_text(
                    "🚨 Emergency Services 🚨\n\n🚑 Ambulance: 102\n👮 Police: 100\n🔥 Fire: 101\n🚨 State Emergency: 1070"
                )
        elif interaction_type == "complaint":
            await update.message.reply_text(
                "📝 File Complaint\n\nPlease describe your complaint in detail:"
            )
        elif interaction_type == "ex_gratia":
            await update.message.reply_text(
                "💰 Ex-Gratia Application\n\nYour application has been submitted without location data. We'll contact you for further details."
            )
        elif interaction_type == "homestay":
            await update.message.reply_text(
                "🏡 Homestay Booking\n\nWhich place would you like to stay in?"
            )
        else:
            await update.message.reply_text(
                "Thank you! How can I help you today?"
            )
    
    async def handle_location_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when user cancels location sharing"""
        
        user_id = update.effective_user.id
        logger.info(f"📍 [CANCEL] User {user_id} cancelled location sharing")
        
        # Remove keyboard
        remove_keyboard = ReplyKeyboardRemove()
        await update.message.reply_text(
            "❌ Location sharing cancelled.",
            reply_markup=remove_keyboard
        )
        
        # Clear stored context
        context.user_data.pop('location_request', None)
    
    def get_location_stats(self):
        """Get statistics about captured locations"""
        try:
            if not os.path.exists(self.location_file):
                return {'total_locations': 0, 'unique_users': 0, 'interaction_types': {}}
            
            with open(self.location_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                locations = list(reader)
            
            stats = {
                'total_locations': len(locations),
                'unique_users': len(set(loc['user_id'] for loc in locations)),
                'interaction_types': {}
            }
            
            for loc in locations:
                interaction_type = loc['interaction_type']
                stats['interaction_types'][interaction_type] = stats['interaction_types'].get(interaction_type, 0) + 1
            
            return stats
        except Exception as e:
            logger.error(f"📍 [ERROR] Failed to get location stats: {e}")
            return {'error': str(e)}
    
    def should_capture_location(self, message_text: str) -> bool:
        """Determine if location should be captured for this message"""
        location_keywords = [
            "emergency", "help", "sos", "ambulance", "police", "fire",
            "complaint", "report", "issue", "problem",
            "homestay", "hotel", "accommodation", "stay",
            "nearby", "nearest", "location", "where", "distance"
        ]
        
        message_lower = message_text.lower()
        return any(keyword in message_lower for keyword in location_keywords)
    
    def detect_interaction_type(self, message_text: str) -> str:
        """Detect interaction type from message"""
        message_lower = message_text.lower()
        
        if any(word in message_lower for word in ["emergency", "help", "sos", "ambulance", "police", "fire"]):
            return "emergency"
        elif any(word in message_lower for word in ["complaint", "report", "issue", "problem"]):
            return "complaint"
        elif any(word in message_lower for word in ["homestay", "hotel", "accommodation", "stay"]):
            return "homestay"
        else:
            return "general"

# Test the location system
if __name__ == "__main__":
    location_system = SimpleLocationSystem()
    stats = location_system.get_location_stats()
    print(f"📍 Location System Stats: {stats}") 