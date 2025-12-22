const { MongoClient } = require('mongodb');

// Production MongoDB connection string
const MONGO_URI = 'mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster';
const DB_NAME = 'debtor_portal';

async function getRecentOTPs() {
    const client = new MongoClient(MONGO_URI);
    
    try {
        console.log('🔍 Fetching last 5 OTPs from production database...\n');
        console.log('='.repeat(70));
        
        await client.connect();
        const db = client.db(DB_NAME);
        const otps = db.collection('otps');
        
        // Get last 5 OTPs sorted by creation time (newest first)
        const recentOTPs = await otps.find({})
            .sort({ created_at: -1 })
            .limit(5)
            .toArray();
        
        if (recentOTPs.length === 0) {
            console.log('❌ No OTPs found in database');
            return;
        }
        
        console.log(`\n📧 Last ${recentOTPs.length} OTP(s) Generated:\n`);
        console.log('='.repeat(70));
        
        recentOTPs.forEach((record, index) => {
            const createdAt = record.created_at ? new Date(record.created_at).toLocaleString() : 'Unknown';
            console.log(`\n${index + 1}. 🔑 OTP: ${record.otp}`);
            console.log(`   📧 Email: ${record.email}`);
            console.log(`   🆔 National ID: ${record.national_id}`);
            console.log(`   🕐 Created: ${createdAt}`);
            console.log('-'.repeat(70));
        });
        
        console.log('\n✅ Use these OTPs to login (valid for 5 minutes from creation time)');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    } finally {
        await client.close();
    }
}

getRecentOTPs();
