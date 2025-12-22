const { MongoClient } = require('mongodb');

const MONGODB_URI = 'mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster';

async function findDebtorEmail() {
    const client = new MongoClient(MONGODB_URI);
    
    try {
        await client.connect();
        console.log('🔍 Searching for National ID: 1100100051224');
        console.log('=' .repeat(60));
        
        const db = client.db('debtor_portal');
        const debtors = db.collection('debtors');
        
        // Search by national_id
        const debtor = await debtors.findOne({ 
            national_id: '1100100051224' 
        });
        
        if (debtor) {
            console.log('✅ Debtor Found!');
            console.log('');
            console.log('Details:');
            console.log(`   Name: ${debtor.name || 'N/A'}`);
            console.log(`   National ID: ${debtor.national_id}`);
            console.log(`   Email: ${debtor.email || 'N/A'}`);
            console.log(`   Account Number: ${debtor.account_number || 'N/A'}`);
            console.log(`   Case ID: ${debtor.case_id || 'N/A'}`);
            console.log('');
            
            if (debtor.email) {
                console.log('📧 Ready to send OTP to:', debtor.email);
                return debtor.email;
            } else {
                console.log('⚠️  No email found for this debtor');
                return null;
            }
        } else {
            console.log('❌ Debtor not found with National ID: 1100100051224');
            console.log('');
            console.log('Checking if debtor exists with different field name...');
            
            // Try searching with case_id
            const debtorByCaseId = await debtors.findOne({ 
                case_id: '1100100051224' 
            });
            
            if (debtorByCaseId) {
                console.log('✅ Found by case_id!');
                console.log(`   Email: ${debtorByCaseId.email || 'N/A'}`);
                return debtorByCaseId.email;
            }
            
            return null;
        }
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        return null;
    } finally {
        await client.close();
    }
}

findDebtorEmail()
    .then(email => {
        if (email) {
            console.log('');
            console.log('=' .repeat(60));
            console.log('✅ Email found:', email);
            console.log('📧 OTP will be sent from: hello@poweramc.co');
            console.log('📧 OTP will be sent to:', email);
        }
        process.exit(0);
    })
    .catch(error => {
        console.error('Error:', error);
        process.exit(1);
    });
